from __future__ import annotations

from typing import List, Dict, Any, Optional
import os
import math

import chromadb
from chromadb.config import Settings
try:
    from sentence_transformers import SentenceTransformer, util as st_util
except Exception:  # offline or missing deps
    SentenceTransformer = None  # type: ignore
    st_util = None  # type: ignore


def _cosine(a, b):
    if st_util is None:
        return 0.0
    return float(st_util.cos_sim(a, b).cpu().numpy()[0][0])


class Retriever:
    def __init__(self, persist_dir: str = "data/chroma", embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        try:
            os.makedirs(persist_dir, exist_ok=True)
        except OSError as e:
            raise ValueError(f"Cannot create or access persist_dir '{persist_dir}': {e}")
        self.client = chromadb.PersistentClient(path=persist_dir, settings=Settings(allow_reset=False))
        # Lazy init collections
        self._collections = {}
        # Multilingual embedding model (optional offline); lazy load to speed init
        self.model = None
        self._embedding_model_name = embedding_model

    def _col(self, name: str):
        if name not in self._collections:
            try:
                self._collections[name] = self.client.get_collection(name)
            except Exception:
                self._collections[name] = self.client.create_collection(name)
        return self._collections[name]

    def _ensure_model(self):
        if self.model is None and SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(self._embedding_model_name)
            except Exception:
                self.model = None

    def _embed(self, text: str):
        self._ensure_model()
        if self.model is None:
            return None
        return self.model.encode([text], convert_to_tensor=True)

    def _embed_list(self, texts: List[str]):
        self._ensure_model()
        if self.model is None:
            return None
        return self.model.encode(texts, convert_to_tensor=True)

    def search_pdf(self, query: str, k: int = 6) -> List[Dict[str, Any]]:
        """Search PDF text chunks, figure captions, and tables; returns hits with citations."""
        query_vec = self._embed(query)
        hits: List[Dict[str, Any]] = []

        for col_name in ["pdf_chunks", "figure_captions", "table_extracts"]:
            col = self._col(col_name)
            # Query by embedding if possible
            try:
                if query_vec is not None:
                    # Pull all metadata to manually rerank (robust for mixed setups)
                    results = col.query(query_embeddings=query_vec.cpu().numpy().tolist(), n_results=min(k, 10))
                else:
                    results = col.query(query_texts=[query], n_results=min(k, 10))
            except Exception:
                results = {"documents": [[]], "metadatas": [[]], "ids": [[]]}

            # Safely extract result lists
            docs = (results or {}).get("documents") or [[]]
            mds = (results or {}).get("metadatas") or [[]]
            ids = (results or {}).get("ids") or [[]]
            docs = docs[0] if isinstance(docs, list) and docs else []
            mds = mds[0] if isinstance(mds, list) and mds else []
            ids = ids[0] if isinstance(ids, list) and ids else []

            if docs:
                # Try to get embeddings from ChromaDB results if available
                emb = (results or {}).get("embeddings")
                doc_embs = None
                if isinstance(emb, list) and emb:
                    # Some vector stores return [[...], [...]] shape; take first list if so
                    doc_embs = emb[0] if isinstance(emb[0], list) else emb
                if not doc_embs:
                    # Fall back to re-embedding if not available
                    doc_embs = self._embed_list(docs)

                for i, (d, m, _id) in enumerate(zip(docs, mds, ids)):
                    if query_vec is not None and doc_embs is not None:
                        score = _cosine(query_vec, doc_embs[i])
                    else:
                        score = 0.0
                    hits.append({
                        "type": col_name,
                        "text": d,
                        "metadata": m or {},
                        "id": _id,
                        "score": score,
                        "citation": {
                            "doc": (m or {}).get("doc"),
                            "page": (m or {}).get("page"),
                            "figure_id": (m or {}).get("figure_id"),
                            "table_id": (m or {}).get("table_id"),
                        },
                    })

        # Sort across modalities
        hits.sort(key=lambda x: x["score"], reverse=True)
        return hits[:k]

    def search_datasets(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search dataset cards and return dataset_ids with scores and metadata."""
        query_vec = self._embed(query)
        col = self._col("dataset_cards")

        try:
            if query_vec is not None:
                results = col.query(query_embeddings=query_vec.cpu().numpy().tolist(), n_results=min(k, 10))
            else:
                results = col.query(query_texts=[query], n_results=min(k, 10))
        except Exception:
            results = {"documents": [[]], "metadatas": [[]], "ids": [[]]}

        docs = (results or {}).get("documents") or [[]]
        mds = (results or {}).get("metadatas") or [[]]
        ids = (results or {}).get("ids") or [[]]
        docs = docs[0] if isinstance(docs, list) and docs else []
        mds = mds[0] if isinstance(mds, list) and mds else []
        ids = ids[0] if isinstance(ids, list) and ids else []

        hits: List[Dict[str, Any]] = []
        if docs:
            emb = (results or {}).get("embeddings")
            doc_embs = None
            if isinstance(emb, list) and emb:
                doc_embs = emb[0] if isinstance(emb[0], list) else emb
            if not doc_embs:
                doc_embs = self._embed_list(docs)

            for i, (d, m, _id) in enumerate(zip(docs, mds, ids)):
                if query_vec is not None and doc_embs is not None:
                    score = _cosine(query_vec, doc_embs[i])
                else:
                    score = 0.0
                hits.append({
                    "dataset_id": (m or {}).get("dataset_id") or _id,
                    "text": d,
                    "metadata": m or {},
                    "id": _id,
                    "score": score,
                })

        hits.sort(key=lambda x: x["score"], reverse=True)
        return hits[:k]
