Decipher Energy Scenarios – Retrieval Upgrade
============================================

This upgrade adds hybrid RAG, multilingual embeddings, dataset provenance, and a sandboxed plotting tool.

What’s New
- Retrieval: Chroma indices for PDF chunks, figure captions, table extracts, and dataset cards.
- Multilingual search: Sentence-Transformers model for query embeddings and reranking.
- PDF ingestion: Production-style ingestor that emits Records and saves table TSVs and figure PNGs (best-effort if `unstructured` is installed).
- Dataset catalog: Scans CSVs and creates dataset cards with schema and units.
- Plot tool: FastAPI service that renders figures from a JSON spec and returns PNG + derived CSV.
- Agents/UI: DocumentIntelligenceAgent and DataInterpreterAgent use the Retriever; Streamlit shows source cards and a "Recreate this figure" helper.

Install
1) Base deps
   - Ensure Python 3.10+
   - `pip install -r requirements.txt`
   - Optional for PDF/plot service: `pip install fastapi uvicorn`

2) Index build extras (optional but recommended for best coverage)
   - `pip install -r requirements-index.txt`
   - Notes:
     - `unstructured` enables figure/table caption extraction; some hi_res features may require system packages.
     - `pymupdf` (fitz) improves image extraction from PDFs.

3) Environment
   - Add to `.env` your `OPENAI_API_KEY` and ensure `DATA_PATH` and `REPORTS_PATH` are set appropriately in `src/utils/config.py`.

Build Index
- Ingest PDFs and datasets and persist Chroma collections to `data/chroma`:
  - `python tasks/build_index.py --reports data/reports --data_root data --persist data/chroma --fresh --reset`

Run Plot Tool
- Start the service on localhost:9000:
  - `uvicorn services.plot_tool:app --reload --port 9000`
- Endpoint: `POST /plot` with JSON body:
  ```json
  {
    "dataset_id": "04-02-final_energy_consumption_by_purpose_fuel.csv",
    "filters": {"scenario": ["ZERO-Basis"]},
    "transforms": {"groupby": ["year", "scenario"], "agg": "sum"},
    "chart": {"type": "line", "x": "year", "y": "value", "color": "scenario"}
  }
  ```
  Returns `{ ok, png_base64, csv, spec }`.

Chat API (experimental)
- Start the chat service on localhost:9001:
  - `uvicorn services.chat_api:app --reload --port 9001`
- Endpoints:
  - `POST /chat` → `{ ok, content, confidence, data_sources, suggestions, agents_involved }`
  - `GET /chat/stream?query=...&user_type=...` → SSE stream of tokens; final `event: meta` contains metadata.

Files API (open PDFs at page)
- Start the files service on localhost:9002:
  - `uvicorn services.files_api:app --reload --port 9002`
- Endpoints:
  - `GET /files/raw?path=...` → serves a local PDF/CSV if path is inside allowed data folders
  - `GET /files/pdf_view?path=...&page=N` → HTML viewer that opens the PDF at the requested page

Use in Streamlit
- `streamlit run streamlit_app.py`
- Ask a question. The agents perform semantic search first.
- The "Source Cards" section shows citations from PDFs or datasets.
- The "Recreate This Figure" panel pre-fills a plot spec and can POST to `plot_tool` if it’s running.

Notes
- The ingestion uses a PyPDF2 fallback; enabling `unstructured` improves figure/table capture but is optional.
- Multilingual model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` is used by default; change in `src/retrieval/retriever.py` if desired.
- Collections: `pdf_chunks`, `figure_captions`, `table_extracts`, `dataset_cards` in `data/chroma`.
