from __future__ import annotations

import base64
import io
from typing import Dict, Any, Optional, List

import pandas as pd
import matplotlib
# Force non-GUI backend to avoid macOS NSWindow errors in server threads
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import os
import json

# Local imports
from src.data_processors.dataset_catalog import DatasetCatalog


class PlotSpec(BaseModel):
    dataset_id: str
    filters: Optional[Dict[str, Any]] = None
    transforms: Optional[Dict[str, Any]] = None
    chart: Dict[str, Any]


import re

def load_dataset_by_id(data_root: str, dataset_id: str, max_file_size: int = 10_000_000, max_rows: int = 100_000) -> pd.DataFrame:
    # Validate DATA_ROOT
    if not os.path.exists(data_root) or not os.path.isdir(data_root):
        raise HTTPException(status_code=400, detail=f"DATA_ROOT '{data_root}' does not exist or is not a directory")
    # Sanitize dataset_id
    if not re.fullmatch(r"[A-Za-z0-9_.\-]+", dataset_id):
        raise HTTPException(status_code=400, detail=f"Invalid dataset_id '{dataset_id}'")
    catalog = DatasetCatalog(data_root)
    found_path = None
    for cat, names in catalog.list_csvs().items():
        if dataset_id in names:
            candidate_path = os.path.join(catalog.synth_dir if cat == "synthesis" else catalog.trans_dir, dataset_id)
            abs_candidate = os.path.realpath(candidate_path)
            abs_root = os.path.realpath(data_root)
            if abs_candidate.startswith(abs_root):
                found_path = abs_candidate
                break
    if not found_path:
        raise FileNotFoundError(f"Dataset {dataset_id} not found")
    # File size safeguard
    if os.path.getsize(found_path) > max_file_size:
        raise HTTPException(status_code=413, detail=f"Dataset file too large (>{max_file_size} bytes)")
    # Row count and load safeguard: read up to max_rows+1 rows
    df = pd.read_csv(found_path, nrows=max_rows+1)
    if len(df) > max_rows:
        raise HTTPException(status_code=413, detail=f"Dataset has too many rows (>{max_rows})")
    return df


def apply_filters(df: pd.DataFrame, filters: Optional[Dict[str, Any]]) -> pd.DataFrame:
    if not filters:
        return df
    for col, val in filters.items():
        if col in df.columns:
            if isinstance(val, list):
                df = df[df[col].isin(val)]
            else:
                df = df[df[col] == val]
    return df


def apply_transforms(df: pd.DataFrame, transforms: Optional[Dict[str, Any]]) -> pd.DataFrame:
    if not transforms:
        return df
    # Minimal transforms: groupby and aggregate
    if "groupby" in transforms and isinstance(transforms["groupby"], list):
        group_cols = [c for c in transforms["groupby"] if c in df.columns]
        if group_cols and "value" in df.columns:
            agg = transforms.get("agg", "sum")
            if agg == "mean":
                df = df.groupby(group_cols, as_index=False)["value"].mean()
            else:
                df = df.groupby(group_cols, as_index=False)["value"].sum()
    return df


def plot_chart(df: pd.DataFrame, chart: Dict[str, Any]) -> bytes:
    plt.figure(figsize=(6, 4), dpi=150)
    kind = chart.get("type", "line")
    x = chart.get("x") or ("year" if "year" in df.columns else None)
    y = chart.get("y") or ("value" if "value" in df.columns else None)
    hue = chart.get("color") or chart.get("hue")

    if not x or not y or x not in df.columns or y not in df.columns:
        raise HTTPException(status_code=400, detail="Chart spec requires valid 'x' and 'y' columns")

    if kind in ("line", "area"):
        if hue and hue in df.columns:
            for label, sub in df.groupby(hue):
                plt.plot(sub[x], sub[y], label=str(label))
        else:
            plt.plot(df[x], df[y])
        if kind == "area":
            plt.fill_between(df[x], df[y], alpha=0.2)
    elif kind == "bar":
        if hue and hue in df.columns:
            # simple stacked bar by hue
            pivot = df.pivot_table(index=x, columns=hue, values=y, aggfunc="sum", fill_value=0)
            pivot.plot(kind="bar", stacked=True)
        else:
            plt.bar(df[x], df[y])
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported chart type: {kind}")

    plt.xlabel(x)
    plt.ylabel(y)
    if hue and hue in df.columns:
        plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return buf.read()


app = FastAPI(title="Plot Tool", version="0.1.0")


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/plot")
def plot_endpoint(spec: PlotSpec):
    data_root = os.environ.get("DATA_ROOT", "data")
    # Validate DATA_ROOT
    if not os.path.exists(data_root) or not os.path.isdir(data_root):
        raise HTTPException(status_code=400, detail=f"DATA_ROOT '{data_root}' does not exist or is not a directory")
    # Validate dataset_id
    if not isinstance(spec.dataset_id, str) or not re.fullmatch(r"[A-Za-z0-9_.\-]+", spec.dataset_id):
        raise HTTPException(status_code=400, detail=f"Invalid dataset_id '{spec.dataset_id}'")
    try:
        df = load_dataset_by_id(data_root, spec.dataset_id)
        df_f = apply_filters(df, spec.filters)
        df_t = apply_transforms(df_f, spec.transforms)
        # Additional row count safeguard before plotting
        if len(df_t) > 100_000:
            raise HTTPException(status_code=413, detail="Transformed dataset too large to plot (>100,000 rows)")
        png_bytes = plot_chart(df_t, spec.chart)
        csv_buf = io.StringIO()
        df_t.to_csv(csv_buf, index=False)
        return {
            "ok": True,
            "png_base64": base64.b64encode(png_bytes).decode("utf-8"),
            "csv": csv_buf.getvalue(),
            "spec": json.loads(spec.model_dump_json())
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# To run: uvicorn services.plot_tool:app --reload --port 9000
