# Multi‑Agent RAG Data Access Architecture

Scope: This document explains how this repository makes PDF, CSV, and (planned) XLSX data accessible to a chatbot, focusing on architecture, data entrypoints, indexing/vector storage (current vs. intended), RAG dataflow, and chatbot features.

Status summary (at a glance)
- Data sources wired today: CSV files under `data/extracted/(synthesis|transformation)` and PDF reports under `data/reports`.
- Retrieval style: Hybrid RAG with Chroma collections and multilingual embeddings; agents use the Retriever (via `search_pdf` and `search_datasets`) for initial retrieval, then LLM summarization with citations.
- PDF handling: Text via PyPDF2, plus optional `unstructured` for figure/table captions (with heuristic fallback). Captions/tables indexed with provenance.
- CSV handling: Pandas loader and catalog; dataset cards indexed with schema/units to map query → dataset.
- XLSX handling: openpyxl present; primary runtime path is CSV.
- UI: Streamlit app with Source Cards and a persistent “Recreate This Figure (last result)” panel; CLI entrypoint also available.


1) High‑level architecture
- Multi‑agent layer (src/agents/)
  - OrchestratorAgent routes a user query to specialist agents in parallel and synthesizes the answer.
  - DataInterpreterAgent analyzes curated CSV datasets and uses the Retriever to map query → dataset ids.
  - DocumentIntelligenceAgent queries the Retriever for grounded PDF excerpts and summarizes with citations.
  - PolicyContextAgent and ScenarioAnalystAgent extend the skill set (not shown here in detail).
- Data processors (src/data_processors/)
  - CSVProcessor handles discovery, loading, filtering, and basic summarization of CSV datasets.
  - PDFProcessor handles listing reports and extracting/searching plain text from PDFs.
  - PDFIngestor (pdf_ingest_unstructured.py) emits Records for `pdf_chunks`, `figure_captions`, `table_extracts` and saves figure/table artifacts.
  - DatasetCatalog builds dataset cards (id, path, schema, units) for indexing.
-- Retrieval (src/retrieval/)
  - Indexer builds/persists Chroma collections: `pdf_chunks`, `figure_captions`, `table_extracts`, `dataset_cards`.
  - Retriever provides multilingual search with reranking across collections.
- Frontends
  - Streamlit web app (streamlit_app.py) for chat‑style interaction and quick stats.
  - CLI (main.py → interfaces/cli_interface.py) for terminal interaction.
- Configuration
  - src/utils/config.py: loads `.env` (OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, MAX_TOKENS) and default paths.


2) Data sources and entrypoints
- CSV (curated):
  - data/extracted/synthesis: thematic, scenario‑aware CSVs (80+ files) used by DataInterpreterAgent.
  - data/extracted/transformation: additional electricity transformation datasets.
  - Entry path in code: CSVProcessor(data_path).get_available_files(), load_csv(), filter_data(), etc.
- PDF reports:
  - data/reports: technical reports, summaries, fact sheets, specialized studies.
  - Entry path in code: PDFProcessor(reports_path).get_available_reports(), extract_text(), search_text().
- XLSX:
  - data/reports includes e.g. 10324-EP2050+_Kurzbericht_Datentabellen_2022-04-12.xlsx. Excel reading is not yet integrated into the runtime agents; conversion to CSV appears to be performed offline/notebook‑driven.
- Scenario results (ZIPs):
  - data/scenario_results: ZIPs with raw or detailed results (not wired to the chatbot runtime).


3) Current ingestion components (runtime)
- CSV ingestion
  - Discovery and loading, with basic caches and helpers for scenario/variant/year filtering.
  - Code excerpt:
    ```python path=/Users/svrueegg/Documents/GIT/decipher-energy-scenarios/src/data_processors/csv_processor.py start=1
    class CSVProcessor:
        def __init__(self, data_path: str):
            self.data_path = data_path
            self.synthesis_path = os.path.join(data_path, "extracted", "synthesis")
            self.transformation_path = os.path.join(data_path, "extracted", "transformation")
            self._cache = {}
        
        def get_available_files(self) -> Dict[str, List[str]]:
            files = {"synthesis": [], "transformation": []}
            if os.path.exists(self.synthesis_path):
                files["synthesis"] = [f for f in os.listdir(self.synthesis_path) if f.endswith('.csv')]
            if os.path.exists(self.transformation_path):
                files["transformation"] = [f for f in os.listdir(self.transformation_path) if f.endswith('.csv')]
            return files
        
        def load_csv(self, filename: str, category: str = "synthesis") -> pd.DataFrame:
            ...
        
        def filter_data(...):
            ...
    ```
- PDF ingestion
  - PyPDF2 text extraction; paragraph‑level regex search; document cataloging lives in DocumentIntelligenceAgent.
  - Code excerpt:
    ```python path=/Users/svrueegg/Documents/GIT/decipher-energy-scenarios/src/data_processors/pdf_processor.py start=1
    class PDFProcessor:
        def __init__(self, reports_path: str):
            self.reports_path = reports_path
            self._cache = {}
        
        def get_available_reports(self) -> List[str]:
            return [f for f in os.listdir(self.reports_path) if f.endswith('.pdf')]
        
        def extract_text(self, pdf_filename: str) -> str:
            with open(os.path.join(self.reports_path, pdf_filename), 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = "".join(page.extract_text() + "\n" for page in pdf_reader.pages)
            self._cache[pdf_filename] = text
            return text
        
        def search_text(self, query: str, pdf_filename: Optional[str] = None) -> Dict[str, List[str]]:
            # Compile a safe pattern: treat query as literal to avoid ReDoS; allow regex via a future flag if needed.
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            max_matches = 50
            matches: List[str] = []
            sources: List[Dict[str, Any]] = []

            def _search_in_text(text: str, src: str) -> None:
                for p in text.split("\n\n"):
                    if pattern.search(p or ""):
                        matches.append(p.strip())
                        sources.append({"file": src})
                        if len(matches) >= max_matches:
                            return

            if pdf_filename:
                text = self._cache.get(pdf_filename) or self.extract_text(pdf_filename)
                _search_in_text(text, pdf_filename)
            else:
                # Iterate per file to control memory and keep provenance.
                files = list(self.get_available_reports())
                for f in files:
                    try:
                        text = self._cache.get(f) or self.extract_text(f)
                        _search_in_text(text, f)
                        if len(matches) >= max_matches:
                            break
                    except Exception as e:
                        # Best-effort: skip unreadable PDFs; consider logging upstream.
                        continue
            return {"matches": matches, "sources": sources}
  - notebooks/extract_pdf_data.ipynb demonstrates unstructured.partition.pdf with strategy="hi_res", infer_table_structure=True, and extract_image_block_to_payload=True. This can yield base64 images and table structures for downstream indexing, but is not integrated into the production agents yet.


4) Chatbot orchestration and runtime dataflow
- Orchestrator‑centric flow
  - The Streamlit app initializes specialist agents and sends the user query to OrchestratorAgent.
  - Orchestrator analyzes the query (via an LLM call) to decide routing to agents (DataInterpreter, DocumentIntelligence, etc.), runs them in parallel, then synthesizes their responses via another LLM call.
- Vector retriever in path
  - The agents call the Retriever: DataInterpreterAgent uses `search_datasets` to map queries to dataset ids, and DocumentIntelligenceAgent uses `search_pdf` to retrieve grounded PDF excerpts. Regex fallback is used only if retrieval fails. The synthesis relies on prompting after retrieval.
- Key code paths
  - Orchestrator routing and synthesis:
    ```python path=/Users/svrueegg/Documents/GIT/decipher-energy-scenarios/src/agents/orchestrator_agent.py start=1
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        routing_decision = await self._analyze_query_routing(query, context)
        agent_responses = await self._route_to_agents(query, routing_decision, context)
        final_response = await self._synthesize_response(query, agent_responses, routing_decision)
        return final_response
    ```
  - DataInterpreterAgent catalogs CSVs and prepares analysis for LLM summarization:
    ```python path=/Users/svrueegg/Documents/GIT/decipher-energy-scenarios/src/agents/data_interpreter_agent.py start=1
    self.csv_processor = CSVProcessor(data_path)
    self.data_catalog = self._build_data_catalog()
    async def _analyze_data(...):
        # loads CSVs, computes stats/trends per file
        ...
    async def _generate_data_response(...):
        # packages analysis as JSON and asks the LLM to narrate the answer
        ...
    ```
  - DocumentIntelligenceAgent catalogs PDFs and performs paragraph search:
    ```python path=/Users/svrueegg/Documents/GIT/decipher-energy-scenarios/src/agents/document_intelligence_agent.py start=1
    self.pdf_processor = PDFProcessor(reports_path)
    self.document_catalog = self._build_document_catalog()
    async def _extract_information(...):
        search_results = self.pdf_processor.search_text(query, filename)
        ...
    ```
- UI integration
  - Streamlit hooks up the orchestrator and displays answer, confidence, sources, suggestions.
  - Code excerpt:
    ```python path=/Users/svrueegg/Documents/GIT/decipher-energy-scenarios/streamlit_app.py start=1
    orchestrator = OrchestratorAgent(config.openai_api_key)
    orchestrator.register_agent(DataInterpreterAgent(...))
    orchestrator.register_agent(DocumentIntelligenceAgent(...))
    response = loop.run_until_complete(orchestrator.process_query(query, context))
    ```


5) Vector storage and indexing (implemented)
- Collections
  - `pdf_chunks`, `figure_captions`, `table_extracts`, `dataset_cards` under `data/chroma`.
  - Metadata examples: `{ doc, page, chunk_id | figure_id | table_id, image_path?, tsv_path?, dataset_id, path, category, schema, units }`.
- Ingestion
  - PDFIngestor (PyPDF2 + optional unstructured; heuristic caption detection fallback).
  - DatasetCatalog → Dataset cards with schema/units.
- Embeddings & reranking
  - Sentence‑Transformers multilingual model; offline fallback uses text query.
- Retriever
  - `search_pdf(query, k)` returns grounded excerpts across modalities with citations (doc,page).
  - `search_datasets(query, k)` returns dataset_ids with scores and metadata.
- Agent integration
  - DocumentIntelligenceAgent uses `search_pdf()` for PDF retrieval before regex fallback.
  - DataInterpreterAgent uses `search_datasets()` for dataset retrieval before heuristic filename/variable matching.


6) Figures, images, and captions indexing
- Runtime
  - `pdf_ingest_unstructured.py` emits figure captions and table extracts (tsv/text), storing artifacts under `data/ingest/{figures,tables}` and indexing metadata.
  - Heuristic caption detection captures common prefixes (Abbildung/Figure/Tabelle/Tab.).
- Optional enhancements
  - Enable full hi_res unstructured pipeline (system deps required) for better image/table extraction.


7) Chatbot features and behavior
- Routing and parallelism: Orchestrator analyzes and parallel‑dispatches to agents, then synthesizes responses.
- Confidence heuristic: Derived from agent‑level signals (e.g., number of relevant files, presence of matches) and simple keyword scoring; capped at 0.9.
- Data provenance: Streamlit shows Source Cards with citations; persistent “Recreate This Figure (last result)” posts to Plot Tool and renders PNG + derived CSV.
- Caching: Streamlit caches initialized agents; processors cache loaded files/text per process.


8) Directory mapping (relevant paths)
- data/reports: PDF and XLSX source documents.
- data/extracted/synthesis: curated CSVs consumed by DataInterpreterAgent.
- data/extracted/transformation: additional CSVs for transformation/electricity.
- data/chroma: Chroma persist directory (RAG indices).
- notebooks/: ETL and PDF extraction experiments; not part of runtime chatbot path.
- src/data_processors/: CSVProcessor, PDFProcessor, PDFIngestor, DatasetCatalog.
- src/agents/: orchestrator and specialist agents.
- src/retrieval/: Indexer and Retriever.
- services/plot_tool.py: FastAPI service for figure rendering.
- streamlit_app.py: UI entrypoint; main.py: CLI entrypoint.


9) Deployment/runtime notes
- Environment (.env supported)
  - `OPENAI_API_KEY=...`
  - `MODEL_NAME=gpt-4o-mini` (BaseAgent reads from env if model not passed)
  - `TEMPERATURE=0.2`, `MAX_TOKENS=1800` (optional)
  - `PLOT_TOOL_URL=http://127.0.0.1:9000` (optional)
- Build RAG indices
  - `python tasks/build_index.py --reports data/reports --data_root data --persist data/chroma --fresh --reset`
  - `--fresh` removes the persist dir; `--reset` clears collections before upsert.
- Start Plot Tool
  - `DATA_ROOT=data uvicorn services.plot_tool:app --reload --port 9000`
  - Health: `GET /healthz`; Plot: `POST /plot`
- Launch options
  - CLI: `python main.py`
  - Web: `streamlit run streamlit_app.py`


10) Current gaps and actionable recommendations
- Deterministic IDs for figure/table records to allow idempotent upserts without `--reset`.
- Enable full hi_res unstructured pipeline with system deps for richer image/table extraction.
- Add read_excel/XLSX support where needed.
- Optional observability: log retrieval hits and surface excerpts inline.


Appendix: Key code references
- Configuration and agent defaults
  ```
  src/utils/config.py:1
  src/agents/base_agent.py:1
  ```
- Orchestrator (routing + synthesis)
  ```python path=/Users/svrueegg/Documents/GIT/decipher-energy-scenarios/src/agents/orchestrator_agent.py start=1
  class OrchestratorAgent(BaseAgent):
      ...
      async def process_query(...):
          routing_decision = await self._analyze_query_routing(...)
          agent_responses = await self._route_to_agents(...)
          return await self._synthesize_response(...)
  ```
- DataInterpreterAgent (CSV analysis + retriever)
  ```
  src/agents/data_interpreter_agent.py:1
  ```
- DocumentIntelligenceAgent (PDF search + retriever)
  ```
  src/agents/document_intelligence_agent.py:1
  ```
- Retrieval and indexing
  ```
  src/retrieval/indexer.py:1
  src/retrieval/retriever.py:1
  src/data_processors/pdf_ingest_unstructured.py:1
  src/data_processors/dataset_catalog.py:1
  ```
- Streamlit UI (entrypoint)
  ```
  streamlit_app.py:1
  ```
