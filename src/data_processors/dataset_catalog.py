from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import pandas as pd

from src.retrieval.indexer import Record


@dataclass
class DatasetCard:
    dataset_id: str
    path: str
    category: str  # synthesis|transformation
    schema: List[str]
    units: List[str]
    description: Optional[str] = None


class DatasetCatalog:
    """Scans the data directory to produce dataset cards used for retrieval and loading."""

    def __init__(self, data_root: str):
        self.data_root = data_root
        self.synth_dir = os.path.join(data_root, "extracted", "synthesis")
        self.trans_dir = os.path.join(data_root, "extracted", "transformation")

    def list_csvs(self) -> Dict[str, List[str]]:
        files = {"synthesis": [], "transformation": []}
        if os.path.isdir(self.synth_dir):
            files["synthesis"] = [f for f in os.listdir(self.synth_dir) if f.lower().endswith(".csv")]
        if os.path.isdir(self.trans_dir):
            files["transformation"] = [f for f in os.listdir(self.trans_dir) if f.lower().endswith(".csv")]
        return files

    def _safe_load_head(self, path: str) -> pd.DataFrame:
        try:
            return pd.read_csv(path, nrows=100)
        except Exception:
            return pd.DataFrame()

    def build_cards(self) -> List[DatasetCard]:
        cards: List[DatasetCard] = []
        for category, names in self.list_csvs().items():
            for name in names:
                path = os.path.join(self.synth_dir if category == "synthesis" else self.trans_dir, name)
                df = self._safe_load_head(path)
                schema = df.columns.tolist()
                units = df["unit"].dropna().unique().tolist() if "unit" in df.columns else []
                dataset_id = name  # use filename as id
                cards.append(DatasetCard(
                    dataset_id=dataset_id,
                    path=path,
                    category=category,
                    schema=schema,
                    units=units,
                    description=None,
                ))
        return cards

    def to_records(self, cards: List[DatasetCard]) -> List[Record]:
        recs: List[Record] = []
        for c in cards:
            text = f"{c.dataset_id} | {c.category} | schema: {', '.join(c.schema)} | units: {', '.join(c.units)}"
            recs.append(Record(
                type="dataset_cards",
                text=text,
                metadata={
                    "id": c.dataset_id,
                    "dataset_id": c.dataset_id,
                    "path": c.path,
                    "category": c.category,
                    "schema": ",".join(c.schema),
                    "units": ",".join(c.units),
                },
            ))
        return recs
