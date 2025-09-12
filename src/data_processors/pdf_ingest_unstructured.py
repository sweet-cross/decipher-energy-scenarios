from collections import deque
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

"""
Production-style PDF ingestion. Uses simple PyPDF2 fallback while allowing
optional integration with `unstructured` if installed to extract tables/figures.

Emits:
- Records for text_chunks, figure_captions, table_extracts
- Saves table TSVs and figure PNGs to disk with provenance metadata
"""

import os
import uuid
from typing import List, Dict, Any, Iterable, DefaultDict
import hashlib
import io

import PyPDF2

try:
    # Optional, not required to run basic pipeline
    from unstructured.partition.pdf import partition_pdf  # type: ignore
    HAS_UNSTRUCTURED = True
except Exception:
    HAS_UNSTRUCTURED = False

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except Exception:
    HAS_FITZ = False

try:
    from PIL import Image as PILImage  # type: ignore
    HAS_PIL = True
except Exception:
    HAS_PIL = False

from src.retrieval.indexer import Record


class PDFIngestor:
    def __init__(self, reports_dir: str, output_dir: str = "data/ingest",
                 min_width: int | None = None,
                 min_height: int | None = None,
                 min_area: int | None = None):
        self.reports_dir = reports_dir
        self.output_dir = output_dir
        self.fig_dir = os.path.join(output_dir, "figures")
        self.tab_dir = os.path.join(output_dir, "tables")
        os.makedirs(self.fig_dir, exist_ok=True)
        os.makedirs(self.tab_dir, exist_ok=True)
        # Heuristics to filter logos/small images (configurable via args/env)
        self.min_img_width = int(min_width if min_width is not None else os.environ.get("MIN_FIGURE_WIDTH", 220))
        self.min_img_height = int(min_height if min_height is not None else os.environ.get("MIN_FIGURE_HEIGHT", 160))
        self.min_img_area = int(min_area if min_area is not None else os.environ.get("MIN_FIGURE_AREA", 60000))

    def _list_pdfs(self) -> List[str]:
        if not os.path.isdir(self.reports_dir):
            return []
        return [f for f in os.listdir(self.reports_dir) if f.lower().endswith(".pdf")]

    def ingest(self) -> List[Record]:
        records: List[Record] = []
        seen_hashes: set = set()  # dedupe exact duplicate images by content hash
        for pdf_name in self._list_pdfs():
            pdf_path = os.path.join(self.reports_dir, pdf_name)
            # Remove extension and sanitize filename for use as doc_id
            doc_id = os.path.splitext(os.path.basename(pdf_name))[0]
            # Replace any remaining path separators or special chars
            doc_id = doc_id.replace("/", "_").replace("\\", "_").replace("..", "_")
            # Pre-extract images per page using PyMuPDF if available
            page_images = self._extract_images_pymupdf(pdf_path, doc_id, seen_hashes) if HAS_FITZ else {}
            fig_count_by_page: Dict[int, int] = {}
            tab_count_by_page: Dict[int, int] = {}
            # Text extraction
            records.extend(self._extract_text_chunks(pdf_path, doc_id))
            # Optional richer extraction
            if HAS_UNSTRUCTURED:
                try:
                    records.extend(self._extract_unstructured(pdf_path, doc_id, page_images, fig_count_by_page, tab_count_by_page, seen_hashes))
                except Exception:
                    # Ignore unstructured errors to keep ingestion robust
                    pass
            # Heuristic captions as a fallback (detects common caption prefixes)
            records.extend(self._extract_heuristic_figures_tables(pdf_path, doc_id, page_images, fig_count_by_page, tab_count_by_page))
            # Any remaining unpaired images: emit as figures with empty captions
            for page, imgs in list(page_images.items()):
                start_idx = fig_count_by_page.get(page, 0)
                next_start = start_idx + 1
                for idx in range(len(imgs)):
                    img_path = imgs.popleft()
                    records.append(Record(
                        type="figure_captions",
                        text="",
                        metadata={
                            "id": f"{doc_id}::p{page}::fig{idx+next_start}",
                            "doc": doc_id,
                            "page": page,
                            "figure_id": idx+next_start,
                            "image_path": img_path,
                        },
                    ))
                if len(imgs) > 0:
                    fig_count_by_page[page] = start_idx + len(imgs)
                # Clear after emission
                page_images[page] = deque()
        return records

    def _extract_text_chunks(self, pdf_path: str, doc_id: str) -> List[Record]:
        recs: List[Record] = []
        try:
            with open(pdf_path, "rb") as fh:
                reader = PyPDF2.PdfReader(fh)
                for pi, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    # Simple chunking by paragraphs
                    for ci, para in enumerate([p.strip() for p in text.split("\n\n") if p.strip()]):
                        recs.append(Record(
                            type="pdf_chunks",
                            text=para,
                            metadata={
                                "id": f"{doc_id}::p{pi+1}::c{ci+1}",
                                "doc": doc_id,
                                "page": pi + 1,
                                "chunk_id": ci + 1,
                            },
                        ))
        except Exception:
            logger.error("Failed to extract text from %s", pdf_path, exc_info=True)
        return recs

    def _extract_unstructured(self, pdf_path: str, doc_id: str, page_images: Dict[int, deque], fig_count_by_page: Dict[int, int], tab_count_by_page: Dict[int, int], seen_hashes: set) -> List[Record]:
        """Optional: leverage unstructured to pull figure captions, tables.
        Saves artifacts to disk and emits records with provenance.
        """
        records: List[Record] = []
        if not HAS_UNSTRUCTURED:
            return records

        try:
            elements = partition_pdf(filename=pdf_path, strategy="hi_res")  # type: ignore
        except Exception:
            elements = partition_pdf(filename=pdf_path, strategy="fast")  # type: ignore
        for el in elements:
            etype = getattr(el, "category", None) or getattr(el, "type", None)
            text = getattr(el, "text", None)
            meta = getattr(el, "metadata", None)
            page_number = getattr(meta, "page_number", None) if meta else None

            if etype and "Table" in str(etype):
                tab_count_by_page[page_number] = tab_count_by_page.get(page_number, 0) + 1
                tab_id = tab_count_by_page[page_number]
                tsv_name = f"{doc_id}_p{page_number}_t{tab_id}.tsv"
                tsv_path = os.path.join(self.tab_dir, tsv_name)
                try:
                    with open(tsv_path, "w", encoding="utf-8") as f:
                        f.write((text or "").replace("\t", " ").replace("\n", "\n"))
                except Exception:
                    pass
                records.append(Record(
                    type="table_extracts",
                    text=text or "",
                    metadata={
                        "id": f"{doc_id}::p{page_number}::tab{tab_id}",
                        "doc": doc_id,
                        "page": page_number,
                        "table_id": tab_id,
                        "tsv_path": tsv_path,
                    },
                ))
            elif etype and ("Figure" in str(etype) or "Image" in str(etype)):
                # Prefer pairing captions with already extracted page images
                fig_count_by_page[page_number] = fig_count_by_page.get(page_number, 0) + 1
                fig_id = fig_count_by_page[page_number]
                img_path = None
                if page_number in page_images and page_images[page_number]:
                    img_path = page_images[page_number].popleft()
                else:
                    # Attempt to persist image payload from unstructured element if available and large enough
                    try:
                        img_obj = getattr(el, "image", None)
                        if img_obj is not None and HAS_PIL:
                            buf = io.BytesIO()
                            img_obj.save(buf, format="PNG")
                            raw = buf.getvalue()
                            if self._is_large_image_bytes(raw):
                                h = hashlib.md5(raw).hexdigest()
                                if h not in seen_hashes:
                                    out_name = f"{doc_id}_p{page_number}_f{fig_id}.png"
                                    img_path = os.path.join(self.fig_dir, out_name)
                                    with open(img_path, "wb") as f:
                                        f.write(raw)
                                    seen_hashes.add(h)
                        else:
                            # base64-like payloads in metadata
                            b64 = None
                            for attr in ["image_base64", "binary_blob", "data"]:
                                b64 = b64 or getattr(meta, attr, None) if meta else None
                            if b64:
                                import base64
                                raw = base64.b64decode(b64)
                                if self._is_large_image_bytes(raw):
                                    h = hashlib.md5(raw).hexdigest()
                                    if h not in seen_hashes:
                                        out_name = f"{doc_id}_p{page_number}_f{fig_id}.png"
                                        img_path = os.path.join(self.fig_dir, out_name)
                                        with open(img_path, "wb") as f:
                                            f.write(raw)
                                        seen_hashes.add(h)
                    except Exception:
                        pass
                records.append(Record(
                    type="figure_captions",
                    text=text or "",
                    metadata={
                        "id": f"{doc_id}::p{page_number}::fig{fig_id}",
                        "doc": doc_id,
                        "page": page_number,
                        "figure_id": fig_id,
                        "image_path": img_path,
                    },
                ))
        return records

    def _extract_heuristic_figures_tables(self, pdf_path: str, doc_id: str, page_images: Dict[int, deque], fig_count_by_page: Dict[int, int], tab_count_by_page: Dict[int, int]) -> List[Record]:
        out: List[Record] = []
        try:
            with open(pdf_path, "rb") as fh:
                reader = PyPDF2.PdfReader(fh)
                for pi, page in enumerate(reader.pages):
                    text = (page.extract_text() or "").strip()
                    if not text:
                        continue
                    for ln in [ln.strip() for ln in text.split("\n") if ln.strip()]:
                        low = ln.lower()
                        pno = pi + 1
                        if low.startswith(("abbildung ", "abb.", "figure ", "fig.")):
                            fig_count_by_page[pno] = fig_count_by_page.get(pno, 0) + 1
                            fig_id = fig_count_by_page[pno]
                            img_path = None
                            out.append(Record(
                                type="figure_captions",
                                text=ln,
                                metadata={
                                    "id": f"{doc_id}::p{pno}::fig{fig_id}",
                                    "doc": doc_id,
                                    "page": pno,
                                    "figure_id": fig_id,
                                    "image_path": img_path,
                                },
                            ))
                        elif low.startswith(("tabelle ", "tab.", "table ")):
                            tab_count_by_page[pno] = tab_count_by_page.get(pno, 0) + 1
                            tab_id = tab_count_by_page[pno]
                            out.append(Record(
                                type="table_extracts",
                                text=ln,
                                metadata={
                                    "id": f"{doc_id}::p{pno}::tab{tab_id}",
                                    "doc": doc_id,
                                    "page": pno,
                                },
                            ))
        except Exception:
            return out
        return out

    def _extract_images_pymupdf(self, pdf_path: str, doc_id: str, seen_hashes: set) -> Dict[int, deque]:
        """Use PyMuPDF to extract images page-by-page. Returns mapping page -> list of saved image paths.
        This is a best-effort, filename-based extraction without coordinates.
        """
        page_images: Dict[int, deque] = {}
        try:
            doc = fitz.open(pdf_path)  # type: ignore
            for pno in range(len(doc)):
                page = doc[pno]
                # Iterate images; get_images returns (xref, smask, width, height, bpc, colorspace, alt, name, filter, decode)
                imgs = page.get_images(full=True)
                if not imgs:
                    continue
                page_list: List[str] = []
                for idx, img in enumerate(imgs, start=1):
                    xref = img[0]
                    try:
                        pix = doc.extract_image(xref)
                        ext = pix.get("ext", "png")
                        img_bytes = pix.get("image")
                        width = pix.get("width")
                        height = pix.get("height")
                        if not img_bytes:
                            continue
                        # Filter small images/logos by dimension/area
                        if (width and height) and (
                            width < self.min_img_width or height < self.min_img_height or (width * height) < self.min_img_area
                        ):
                            continue
                        # Dedupe exact duplicates via md5
                        h = hashlib.md5(img_bytes).hexdigest()
                        if h in seen_hashes:
                            continue
                        out_name = f"{doc_id}_p{pno+1}_f{idx}.{ext}"
                        out_path = os.path.join(self.fig_dir, out_name)
                        with open(out_path, "wb") as f:
                            f.write(img_bytes)
                        seen_hashes.add(h)
                        page_list.append(out_path)
                    except Exception:
                        continue
                if page_list:
                    page_images[pno + 1] = deque(page_list)
            doc.close()
        except Exception:
            return page_images
        return page_images

    def _is_large_image_bytes(self, data: bytes) -> bool:
        """Filter raw image bytes by decoded size and area, using PIL if available."""
        if not data:
            return False
        if HAS_PIL:
            try:
                im = PILImage.open(io.BytesIO(data))
                w, h = im.size
                if w < self.min_img_width or h < self.min_img_height or (w * h) < self.min_img_area:
                    return False
                return True
            except Exception:
                return False
