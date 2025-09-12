"""
Swiss Energy Scenarios Decipher System - Streamlit Web Interface
"""

import streamlit as st
import asyncio
import sys
import os
from typing import Dict, Any
import pandas as pd
# import plotly.express as px  # Optional for future visualizations

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config import config
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.data_interpreter_agent import DataInterpreterAgent
from src.agents.scenario_analyst_agent import ScenarioAnalystAgent
from src.agents.document_intelligence_agent import DocumentIntelligenceAgent
from src.agents.policy_context_agent import PolicyContextAgent
from src.retrieval.retriever import Retriever
from src.agents.base_agent import AgentResponse
import json
import base64
import requests
from urllib.parse import quote
PLOT_TOOL_URL = os.environ.get("PLOT_TOOL_URL", "http://127.0.0.1:9000")
ICON_STYLE = os.environ.get("ICON_STYLE", "emoji").lower()  # emoji | lucide
FILES_TOOL_URL = os.environ.get("FILES_TOOL_URL", "http://127.0.0.1:9002")

# Configure Streamlit page
st.set_page_config(
    page_title="VoltVision",
    page_icon="🇨🇭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Simple CSS for centered landing
st.markdown(
    """
    <style>
    .hero {text-align:center; padding-top: 6vh; padding-bottom: 2vh;}
    .hero h1 {font-size: 2.3rem; margin-bottom: 0.3rem;}
    .hero p {color:#666;}
    .centered {max-width: 900px; margin: 0 auto;}
    .chip {display:inline-block; padding:8px 12px; margin:6px; border-radius:12px; background:#f2f2f7;}
    .src-card:hover {background: #f8fafc;}
    .badge {background:#eef2ff;color:#3730a3;padding:2px 6px;border-radius:10px;font-size:0.85em;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Inject a spinner inside the disabled query input (when initializing)
def _inject_input_spinner_if_needed(ready: bool):
    if ready:
        return
    spinner_svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 50 50'>"
        "<circle cx='25' cy='25' r='20' stroke='%236b7280' stroke-width='6' fill='none' opacity='0.25'/>"
        "<path d='M25 5 a20 20 0 0 1 0 40' stroke='%236b7280' stroke-width='6' fill='none'/>"
        "</svg>"
    )
    css = f"""
    <style>
    input[aria-label="Query"][disabled] {{
        background-image: url('data:image/svg+xml;utf8,{spinner_svg}');
        background-repeat: no-repeat;
        background-position: 8px center;
        background-size: 18px 18px;
        padding-left: 32px;
        color: #6b7280 !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


@st.cache_resource
def get_retriever():
    return Retriever(persist_dir="data/chroma")

@st.cache_resource
def initialize_agents():
    config.validate()
    retriever = get_retriever()
    data_interpreter = DataInterpreterAgent(config.openai_api_key, config.data_path, retriever=retriever)
    scenario_analyst = ScenarioAnalystAgent(config.openai_api_key, config.data_path)
    document_intelligence = DocumentIntelligenceAgent(config.openai_api_key, config.reports_path, retriever=retriever)
    policy_context = PolicyContextAgent(config.openai_api_key)
    orch = OrchestratorAgent(config.openai_api_key)
    orch.register_agent(data_interpreter)
    orch.register_agent(scenario_analyst)
    orch.register_agent(document_intelligence)
    orch.register_agent(policy_context)
    return orch

def _user_type_selector(default: str = "general") -> str:
    left, mid, right = st.columns([1, 2, 1])
    with mid:
        try:
            return st.segmented_control(
                "Tell us about your background",
                options=["general", "citizen", "journalist", "student", "policymaker"],
                default=default,
            )
        except Exception:
            return st.radio(
                "Tell us about your background",
                ["general", "citizen", "journalist", "student", "policymaker"],
                index=["general", "citizen", "journalist", "student", "policymaker"].index(default),
                horizontal=True,
            )

def render_landing():
    st.markdown('<div class="hero centered">🇨🇭<h1>VoltVision</h1><p>Interact with todays energy scenarios for the future of Switzerland.</p></div>', unsafe_allow_html=True)
    user_type = _user_type_selector(st.session_state.get("user_type", "general"))
    st.session_state["user_type"] = user_type

    # Initialize the query key before the widget is created (safe to set)
    if "query_input" not in st.session_state:
        st.session_state["query_input"] = ""
    # If a pending query was set by a button click in the previous run, apply it now
    if "pending_query" in st.session_state:
        st.session_state["query_input"] = st.session_state.pop("pending_query")

    submitted = False
    query = st.session_state.get("query_input", "")
    # Initialization is handled in the sidebar; keep input active here
    ready = True
    with st.form("ask_form"):
        c1, c2 = st.columns([12, 1])
        with c1:
            query = st.text_input(
                "Query",
                key="query_input",
                placeholder=("Ask about data, documents, scenarios…"),
                label_visibility="collapsed",
                disabled=False,
            )
        with c2:
            # Submit button
            submitted = st.form_submit_button(
                "Ask",
                use_container_width=True,
                disabled=False
            )
    if submitted and query.strip():
        process_query(query.strip(), user_type)

    st.write("")
    st.caption("Try one of these:")
    examples = [
        "What is an energy scenario?",
        "Compare ZERO vs WWB for electricity demand",
        "Where do the building heating assumptions come from?",
        "Show final energy consumption by sector",
        "Cite the methodology used for emissions"
    ]
    cols = st.columns(len(examples))
    for i, ex in enumerate(examples):
        if cols[i].button(ex, key=f"ex_{i}"):
            # Defer setting the input until before the widget is created on next run
            st.session_state["pending_query"] = ex
            st.rerun()

def _sidebar():
    with st.sidebar:
        # Trigger agent initialization here and show spinner only once
        with st.spinner("⏳ Initializing agents…"):
            _ = initialize_agents()
        st.header("History")
        hist = st.session_state.get("conversation_history", [])
        if hist:
            for i, entry in enumerate(reversed(hist[-10:])):
                label = entry['query'][:38] + ("…" if len(entry['query']) > 38 else "")
                if st.button(label, key=f"hist_{i}"):
                    # Defer setting the input until before the widget is created on next run
                    st.session_state["pending_query"] = entry['query']
                    st.session_state.last_response = entry['response']
                    st.rerun()
        else:
            st.caption("No history yet.")
        st.divider()
        st.header("Stats")
        try:
            from src.data_processors.csv_processor import CSVProcessor
            cp = CSVProcessor(config.data_path)
            files = cp.get_available_files()
            st.metric("Data Files", len(files.get("synthesis", [])) + len(files.get("transformation", [])))
            st.metric("Synthesis Files", len(files.get("synthesis", [])))
            st.metric("Transformation Files", len(files.get("transformation", [])))
        except Exception:
            pass

def main():
    """Main Streamlit application."""
    
    _sidebar()
    if not st.session_state.get("conversation_history"):
        render_landing()
        return
    
    if st.session_state.get("show_history_answer") and st.session_state.get("last_response"):
        st.session_state["show_history_answer"] = False
        main_col, side_col = st.columns([7, 3])
        with main_col:
            st.subheader("🎯 Answer (from history)")
            st.write(st.session_state["last_response"]["content"])
            if st.session_state["last_response"].get("retrieval_method"):
                badge_text = st.session_state["last_response"]["retrieval_method"].replace("_", " ").title()
                st.markdown(f'<span class="badge">{badge_text}</span>', unsafe_allow_html=True)
            # Follow-up ideas (if any) below answer
            suggestions = st.session_state["last_response"].get("suggestions") or []
            if suggestions:
                st.markdown("---")
                st.subheader("Follow‑up Ideas")
                for suggestion in suggestions:
                    if st.button(f"{suggestion[:56]}…" if len(suggestion) > 56 else suggestion, key=f"hist_sug_{hash(suggestion)}"):
                        st.session_state["pending_query"] = suggestion
                        st.rerun()
        with side_col:
            # Meta header combining confidence + agents
            st.markdown("### Confidence & Agents")
            st.metric("Confidence", f"{st.session_state['last_response']['confidence']:.2f}")
            if st.session_state["last_response"].get("agents_involved"):
                emoji = {"DataInterpreter": "📊", "DocumentIntelligence": "📄", "ScenarioAnalyst": "🔮", "PolicyContext": "🏛️", "Orchestrator": "🧭"}
                badges = " ".join([f"{emoji.get(a, '🤖')} {a}" for a in st.session_state["last_response"]["agents_involved"]])
                st.caption(badges)
            st.subheader("Sources")
            # (Optional) source rendering for history answers could be added here
        return

    # If there is already history, render a compact ask bar at the top
    else:
        st.markdown("<div class='centered'>", unsafe_allow_html=True)
        user_type = _user_type_selector(st.session_state.get("user_type", "general"))
        st.session_state["user_type"] = user_type

        # Ensure query key exists prior to widget creation
        if "query_input" not in st.session_state:
            st.session_state["query_input"] = ""
        # Apply any pending query set by previous button clicks
        if "pending_query" in st.session_state:
            st.session_state["query_input"] = st.session_state.pop("pending_query")

        # Keep input active; initialization handled in sidebar
        ready = True
        with st.form("ask_form_top"):
            c1, c2 = st.columns([12, 1])
            with c1:
                query = st.text_input(
                    "Query",
                    key="query_input",
                    placeholder=("Ask about data, documents, scenarios…"),
                    label_visibility="collapsed",
                    disabled=False,
                )
            with c2:
                # Always show a submit button to avoid Streamlit error
                submitted = st.form_submit_button("Ask", use_container_width=True, disabled=False)
        st.markdown("</div>", unsafe_allow_html=True)
        if submitted and query.strip():
            process_query(query.strip(), user_type)

def process_query(query: str, user_type: str):
    """Process a user query asynchronously."""
    
    # Initialize session state
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    with st.spinner(f"🔄 Processing your query as {user_type}…"):
        try:
            orchestrator = initialize_agents()

            # Prepare context
            context = {"user_type": user_type}

            # Prepare streaming synthesis
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            messages, meta = loop.run_until_complete(
                orchestrator.prepare_streaming_synthesis(query, context)
            )
            loop.close()

            # Stream tokens to placeholder
            placeholder = st.empty()
            content = ""
            loop2 = asyncio.new_event_loop()
            asyncio.set_event_loop(loop2)
            async def _consume():
                nonlocal content
                async for tok in orchestrator.stream_synthesis(messages):
                    if tok:
                        content += tok
                        placeholder.write(content)
            loop2.run_until_complete(_consume())
            loop2.close()

            # Build final response object
            # Fallback to non-streaming call if nothing was streamed
            if not content.strip():
                loop3 = asyncio.new_event_loop()
                asyncio.set_event_loop(loop3)
                full_text = loop3.run_until_complete(orchestrator._call_openai(messages))
                loop3.close()
                content = full_text or ""

            response = AgentResponse(
                content=content,
                confidence=meta.get("avg_confidence", 0.5),
                data_sources=meta.get("data_sources", []),
                reasoning=f"Synthesized from {', '.join(meta.get('agents', []))}",
                suggestions=meta.get("suggestions", []),
                agents_involved=meta.get("agents", []),
            )
            
            # Display results
            st.success("✅ Analysis Complete!")

            # Two-column presentation: main answer (wide) + side panel (confidence, sources, follow-ups)
            main_col, side_col = st.columns([7, 3])

            with main_col:
                st.subheader("🎯 Answer")
                st.write(response.content)
                # Retrieval method badge under answer text
                if getattr(response, 'retrieval_method', None):
                    badge_text = response.retrieval_method.replace("_", " ").title()
                    st.markdown(f'<span class="badge">{badge_text}</span>', unsafe_allow_html=True)
                # Follow-up ideas moved below answer instead of side column
                if response.suggestions:
                    st.markdown("---")
                    st.subheader("Follow‑up Ideas")
                    for suggestion in response.suggestions:
                        if st.button(f"{suggestion[:56]}…" if len(suggestion) > 56 else suggestion, key=f"sug_{hash(suggestion)}"):
                            st.session_state["pending_query"] = suggestion
                            st.rerun()

            with side_col:
                # Meta section combining confidence + agents
                st.markdown("### Confidence & Agents")
                st.metric("Confidence", f"{response.confidence:.2f}")
                if getattr(response, 'agents_involved', None):
                    emoji = {"DataInterpreter": "📊", "DocumentIntelligence": "📄", "ScenarioAnalyst": "🔮", "PolicyContext": "🏛️", "Orchestrator": "🧭"}
                    badges = " ".join([f"{emoji.get(a, '🤖')} {a}" for a in response.agents_involved])
                    st.caption(badges)
                st.subheader("Sources")

                def _pretty_name(name: str) -> str:
                    base = os.path.basename(name.split('#')[0])
                    base = os.path.splitext(base)[0]
                    return base.replace('_', ' ').replace('-', ' ')

                def _parse_source(src: str) -> Dict[str, Any]:
                    info = {"type": "text", "title": src, "page": None, "path": None, "image": None}
                    if isinstance(src, str) and (src.endswith('.png') or src.endswith('.jpg')) and os.path.exists(src):
                        info.update({"type": "figure", "title": _pretty_name(src), "image": src, "path": src})
                        return info
                    if isinstance(src, str) and "#p" in src:
                        doc = src.split('#')[0]
                        page = src.split('#p')[-1]
                        path = os.path.join(config.reports_path, doc)
                        info.update({"type": "pdf", "title": _pretty_name(doc), "page": page, "path": path if os.path.exists(path) else None})
                        return info
                    if isinstance(src, str) and (src.endswith('.csv') or '/' in src):
                        title = _pretty_name(src)
                        # Best-effort link resolution under data/extracted
                        candidates = [
                            os.path.join(config.data_path, 'extracted', 'synthesis', os.path.basename(src)),
                            os.path.join(config.data_path, 'extracted', 'transformation', os.path.basename(src)),
                        ]
                        link = next((p for p in candidates if os.path.exists(p)), None)
                        info.update({"type": "dataset", "title": title, "path": link})
                        return info
                    return info

                def _lucide_svg(name: str, size: int = 18, color: str = "#6b7280") -> str:
                    # Minimal inline SVGs for a few icons (file-text, database, image). Fallback to a dot.
                    paths = {
                        "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
                        "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5"/><path d="M21 12c0 1.7-4 3-9 3s-9-1.3-9-3"/><path d="M21 8c0 1.7-4 3-9 3S3 9.7 3 8"/>',
                        "image": '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10.5" r="1.5"/><path d="m21 15-5-5L5 21"/>',
                        "link": '<path d="M10 13a5 5 0 0 1 0-7l1-1a5 5 0 0 1 7 7l-1 1"/><path d="M14 11a5 5 0 0 1 0 7l-1 1a5 5 0 0 1-7-7l1-1"/>'
                    }
                    d = paths.get(name, paths["link"]) 
                    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{d}</svg>'

                def _icon_html(kind: str) -> str:
                    if ICON_STYLE == "lucide":
                        return {
                            "pdf": _lucide_svg("file-text"),
                            "dataset": _lucide_svg("database"),
                            "figure": _lucide_svg("image"),
                        }.get(kind, _lucide_svg("link"))
                    # emoji fallback
                    return {"pdf": "📄", "dataset": "📊", "figure": "🖼️"}.get(kind, "🔗")

                def _render_pdf_card(info: Dict[str, Any]):
                    # Whole card clickable; opens pdf at page
                    open_url = None
                    if info.get("path") and os.path.isfile(info["path"]):
                        open_url = f"{FILES_TOOL_URL}/files/pdf_view?path={quote(info['path'])}&page={info.get('page') or 1}"
                    icon_html = _icon_html('pdf')
                    title = info.get('title') or 'PDF'
                    page_badge = f"<span class='badge'>Page {info.get('page')}</span>" if info.get('page') else ""
                    body = f"<div style='display:flex;gap:10px;align-items:center;'>{icon_html}<div><div><strong>{title}</strong></div>{page_badge}</div></div>"
                    if open_url:
                        st.markdown(f"<a class='src-card' href='{open_url}' target='_blank'>{body}</a>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='src-card'>{body}</div>", unsafe_allow_html=True)

                def _render_dataset_card(info: Dict[str, Any]):
                    icon_html = _icon_html('dataset')
                    title = info.get('title') or 'Dataset'
                    body = f"<div style='display:flex;gap:10px;align-items:center;'>{icon_html}<div><div><strong>{title}</strong></div></div></div>"
                    link = info.get('path')
                    if link and os.path.isfile(link):
                        link = f"{FILES_TOOL_URL}/files/raw?path={quote(link)}"
                        st.markdown(f"<a class='src-card' href='{link}' target='_blank'>{body}</a>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='src-card'>{body}</div>", unsafe_allow_html=True)

                def _render_figure_card(info: Dict[str, Any]):
                    # Image thumbnail wrapped with link to raw file
                    img = info.get("image")
                    if img and os.path.isfile(img):
                        link = f"{FILES_TOOL_URL}/files/raw?path={quote(img)}"
                        st.markdown(f"<a href='{link}' target='_blank'>", unsafe_allow_html=True)
                        st.image(img, use_column_width=True)
                        st.markdown("</a>", unsafe_allow_html=True)
                        st.caption(info.get("title") or "Figure")
                    else:
                        st.markdown(f"<div class='src-card'>{_icon_html('figure')} <strong>{info.get('title') or 'Figure'}</strong></div>", unsafe_allow_html=True)

                # Unique and group by type for readability
                seen = set()
                pdf_cards, dataset_cards, figure_cards, other_cards = [], [], [], []
                for s in response.data_sources or []:
                    if s in seen:
                        continue
                    seen.add(s)
                    info = _parse_source(s)
                    t = info.get('type')
                    if t == 'pdf':
                        pdf_cards.append(info)
                    elif t == 'dataset':
                        dataset_cards.append(info)
                    elif t == 'figure':
                        figure_cards.append(info)
                    else:
                        other_cards.append(info)

                if pdf_cards:
                    st.caption("PDFs")
                    for it in pdf_cards:
                        _render_pdf_card(it)
                if dataset_cards:
                    st.caption("Datasets")
                    for it in dataset_cards:
                        _render_dataset_card(it)
                if figure_cards:
                    st.caption("Figures")
                    for it in figure_cards:
                        _render_figure_card(it)

                # (Follow-up ideas now displayed under main answer column)
            
            # Store in history
            st.session_state.conversation_history.append({
                "query": query,
                "user_type": user_type,
                "response": {
                    "content": response.content,
                    "confidence": response.confidence,
                    "data_sources": response.data_sources or [],
                    "suggestions": response.suggestions or [],
                    "agents_involved": getattr(response, 'agents_involved', [])
                }
            })
            # Persist last response for UI panels on rerun
            st.session_state["last_response"] = {
                "content": response.content,
                "confidence": response.confidence,
                "data_sources": response.data_sources or [],
                "suggestions": response.suggestions or [],
                "reasoning": response.reasoning or "",
                "agents_involved": getattr(response, 'agents_involved', [])
            }
            
        except Exception as e:
            st.error(f"❌ Error processing query: {str(e)}")
            st.info("Please check your configuration and try again.")

if __name__ == "__main__":
    main()
