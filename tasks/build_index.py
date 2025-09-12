from __future__ import annotations
def _rmtree_onerror(func, path, exc_info):
    """Raise errors during rmtree so permission/readonly problems surface."""
    raise exc_info[1]
#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import os
import shutil
from typing import List

from src.retrieval.indexer import Indexer, Record
from src.data_processors.pdf_ingest_unstructured import PDFIngestor
from src.data_processors.dataset_catalog import DatasetCatalog
from src.utils.config import Config


def main():
    parser = argparse.ArgumentParser(description="Build Chroma indices from PDFs and datasets")
    parser.add_argument("--reports", default="data/reports", help="Directory with PDF reports")
    parser.add_argument("--data_root", default="data", help="Root data directory")
    parser.add_argument("--persist", default="data/chroma", help="Chroma persist directory")
    parser.add_argument("--reset", action="store_true", help="Reset existing collections before indexing")
    parser.add_argument("--fresh", action="store_true", help="Delete the persist directory before building")

    args = parser.parse_args()

    # Normalize path-like arguments
    path_args = [
        'reports',
        'data_root',
        'persist',
    ]
    for arg_name in path_args:
        val = getattr(args, arg_name, None)
        if isinstance(val, str):
            norm = os.path.expandvars(os.path.expanduser(val))
            abs_path = os.path.abspath(norm)
            setattr(args, arg_name, abs_path)

    # Fresh build: remove persist directory entirely
    if args.fresh:
        # Safety: refuse to delete suspiciously broad paths.
        persist_ap = os.path.abspath(args.persist)
        if persist_ap in ("/", os.path.expanduser("~")) or len(os.path.normpath(persist_ap).split(os.sep)) < 3:
            raise RuntimeError(f"Refusing to delete unsafe persist path: {persist_ap}")
        if os.path.exists(persist_ap):
            if not os.path.isdir(persist_ap):
                raise RuntimeError(f"Persist path exists but is not a directory: {persist_ap}")
            print(f"[build_index] Removing persist dir: {persist_ap}")
            shutil.rmtree(persist_ap, onerror=_rmtree_onerror)
        os.makedirs(persist_ap, exist_ok=True)
        # Also remove previously ingested artifacts to avoid stale images/tables
        artifacts = [
            os.path.join(args.data_root, "ingest", "figures"),
            os.path.join(args.data_root, "ingest", "tables"),
        ]
        for d in artifacts:
            ap = os.path.abspath(d)
            data_root_ap = os.path.abspath(args.data_root)
            if os.path.commonpath([ap, data_root_ap]) != data_root_ap:
                raise RuntimeError(f"Refusing to delete path outside data_root: {ap}")
            if os.path.isdir(ap):
                print(f"[build_index] Removing artifacts dir: {ap}")
                shutil.rmtree(ap, ignore_errors=True)

    indexer = Indexer(persist_dir=args.persist)

    if args.reset:
        for name in ["pdf_chunks", "figure_captions", "table_extracts", "dataset_cards"]:
            indexer.reset_collection(name)

    # Ingest PDFs
    print("[build_index] Ingesting PDFs from", args.reports)
    if not os.path.isdir(args.reports):
        raise FileNotFoundError(f"Reports directory not found: {args.reports}")
    os.makedirs(os.path.join(args.data_root, "ingest"), exist_ok=True)
    # Load thresholds from config/env (does not require API key)
    cfg = Config.from_env()
    ingestor = PDFIngestor(
        args.reports,
        output_dir=os.path.join(args.data_root, "ingest"),
        min_width=cfg.min_figure_width,
        min_height=cfg.min_figure_height,
        min_area=cfg.min_figure_area,
    )
    pdf_records: List[Record] = ingestor.ingest()
    indexer.upsert_records(pdf_records)
    print(f"[build_index] Indexed {len(pdf_records)} PDF-derived records")

    # Dataset cards
    print("[build_index] Cataloging datasets in", args.data_root)
    catalog = DatasetCatalog(args.data_root)
    cards = catalog.build_cards()
    ds_records = catalog.to_records(cards)
    indexer.upsert_records(ds_records)
    print(f"[build_index] Indexed {len(ds_records)} dataset cards")

    print("[build_index] Done. Collection counts:")
    print(indexer.stats())


if __name__ == "__main__":
    main()
