from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Iterable
import os
import uuid

import chromadb
from chromadb.config import Settings


class _ZeroEmbed:
    def __init__(self, dim: int = 384):
        if dim <= 0:
            raise ValueError("Embedding dimension must be positive")
        self.dim = dim

    def __call__(self, input):
        # Accept strings or list of strings
        if isinstance(input, str):
            n = 1
        elif isinstance(input, (list, tuple)):
            n = len(input)
        else:
            raise TypeError(f"Expected str or list of strings, got {type(input)}")
        return [[0.0] * self.dim for _ in range(n)]

@dataclass
class Record:
    """Generic record for indexing.

    Types:
    - pdf_chunks: PDF text chunks with provenance (doc, page, chunk_id)
    - figure_captions: figure caption with provenance (doc, page, figure_id, image_path)
    - table_extracts: table text/tsv with provenance (doc, page, table_id, tsv_path)
    - dataset_cards: dataset metadata for CSV/XLSX (dataset_id, path, schema, units)
    """

    type: str
    text: str
    metadata: Dict[str, Any]


class Indexer:
    """Builds and maintains Chroma indices for hybrid RAG."""

    def __init__(self, persist_dir: str = "data/chroma"):
        os.makedirs(persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir, settings=Settings(allow_reset=True))

        # Collections for different modalities
        self.collections = {
            "pdf_chunks": self._get_or_create("pdf_chunks"),
            "figure_captions": self._get_or_create("figure_captions"),
            "table_extracts": self._get_or_create("table_extracts"),
            "dataset_cards": self._get_or_create("dataset_cards"),
        }

    def reset_collection(self, name: str):
        try:
            self.client.delete_collection(name)
        except chromadb.errors.NotFoundError:
            pass  # Collection doesn't exist, proceed to create

    def _get_or_create(self, name: str):
        try:
            collection = self.client.get_collection(name)
        except chromadb.errors.NotFoundError:
            collection = self.client.create_collection(name, embedding_function=_ZeroEmbed())
        return collection
    def upsert_records(self, records: Iterable[Record]):
        buckets: Dict[str, Dict[str, List[Any]]] = {}
        for rec in records:
            if not rec.text:
                continue  # Skip empty text records

            if rec.type not in self.collections:
                # Skip unknown types
                continue

            bucket = buckets.setdefault(rec.type, {"ids": [], "documents": [], "metadatas": []})
            record_id = rec.metadata.get("id") if rec.metadata else None
            bucket["ids"].append(record_id or str(uuid.uuid4()))
            bucket["documents"].append(rec.text)
            bucket["metadatas"].append(rec.metadata or {})

        for c_name, payload in buckets.items():
            if payload["ids"]:
                self.collections[c_name] = self._get_or_create(c_name)
                try:
                    self.collections[c_name].upsert(**payload)
                except Exception as e:
                    # Log or re-raise with context
                    raise RuntimeError(f"Failed to upsert records to collection '{c_name}': {e}")

    def ensure_collections(self):
        # Touch all collections to ensure they exist
        for name in list(self.collections.keys()):
            self.collections[name] = self._get_or_create(name)

    def stats(self) -> Dict[str, Any]:
        s = {}
        for name, col in self.collections.items():
            try:
                s[name] = col.count()
            except Exception:
                s[name] = 0
        return s
