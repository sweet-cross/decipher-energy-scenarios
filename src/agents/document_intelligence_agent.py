from typing import Dict, Any, List, Optional
import json
import os
from agents.base_agent import BaseAgent, AgentResponse
from data_processors.pdf_processor import PDFProcessor
from retrieval.retriever import Retriever

class DocumentIntelligenceAgent(BaseAgent):
    def __init__(self, openai_api_key: str, reports_path: str, retriever: Optional[object] = None):
        super().__init__(
            name="DocumentIntelligence", 
            description="Processes PDF reports and extracts knowledge from technical documents",
            openai_api_key=openai_api_key
        )
        self.pdf_processor = PDFProcessor(reports_path)
        # Hybrid RAG retriever (multimodal within PDFs)
        self.retriever = retriever or Retriever(persist_dir="data/chroma")
        self.document_catalog = self._build_document_catalog()
        
    def _build_system_prompt(self) -> str:
        return """You are the Document Intelligence Agent for Swiss Energy Scenarios analysis.

Your expertise includes:
- Processing technical reports and policy documents
- Extracting methodologies, assumptions, and key findings
- Cross-referencing information across multiple documents
- Explaining complex technical concepts in accessible language
- Identifying sources and citations for fact-checking

Available Document Types:
1. Technical Reports (Technischer Bericht)
   - Detailed methodologies and assumptions
   - Modeling approaches and validation
   - Sectoral analysis and projections

2. Executive Summaries (Kurzbericht)
   - Key findings and policy implications
   - High-level scenario comparisons
   - Stakeholder-focused insights

3. Fact Sheets (Faktenblatt)
   - Concise data presentations
   - Policy-relevant statistics
   - Public communication materials

4. Specialized Studies (Exkurs)
   - Deep-dives on specific topics
   - Sensitivity analyses
   - Technology assessments

Document Processing Capabilities:
- Multi-language support (German, French, English)
- Technical terminology interpretation
- Cross-document fact verification
- Citation and source tracking
- Context-aware information extraction

When processing documents:
1. Always cite specific document sources
2. Distinguish between facts, assumptions, and projections
3. Explain methodology and data limitations
4. Provide page references where possible
5. Flag uncertainties and confidence levels
6. Relate findings to broader energy policy context

Response format:
- Lead with direct answer to the query
- Provide supporting evidence with citations
- Explain technical concepts clearly
- Include confidence assessment
- Suggest related document sections
"""
        
    def _build_document_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Build catalog of available documents."""
        catalog = {}
        
        try:
            available_reports = self.pdf_processor.get_available_reports()
            
            for report in available_reports:
                try:
                    summary = self.pdf_processor.get_document_summary(report)
                    
                    # Categorize document type
                    doc_type = self._categorize_document(report)
                    
                    catalog[report] = {
                        "type": doc_type,
                        "summary": summary,
                        "language": self._detect_language(report)
                    }
                    
                except Exception as e:
                    print(f"Error cataloging {report}: {e}")
                    
        except Exception as e:
            print(f"Error building document catalog: {e}")
            
        return catalog
    
    def _categorize_document(self, filename: str) -> str:
        """Categorize document type based on filename."""
        filename_lower = filename.lower()
        
        if 'kurzbericht' in filename_lower or 'summary' in filename_lower:
            return "Executive Summary"
        elif 'technischer' in filename_lower or 'technical' in filename_lower:
            return "Technical Report"
        elif 'faktenblatt' in filename_lower or 'fact' in filename_lower:
            return "Fact Sheet"
        elif 'exkurs' in filename_lower:
            return "Specialized Study"
        elif 'stellungnahmen' in filename_lower:
            return "Stakeholder Input"
        else:
            return "General Report"
    
    def _detect_language(self, filename: str) -> str:
        """Detect document language from filename."""
        if '_DE' in filename or 'deutsch' in filename.lower():
            return "German"
        elif '_FR' in filename or 'french' in filename.lower():
            return "French"  
        elif '_EN' in filename or 'english' in filename.lower():
            return "English"
        else:
            return "German"  # Default assumption for Swiss documents
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Process document intelligence query."""
        # First try semantic retrieval over PDFs (chunks, figures, tables)
        hits = []
        try:
            hits = self.retriever.search_pdf(query, k=6)
        except Exception as e:
            print(f"Retrieval error for query '{query}': {e}")
            hits = []

        if hits:
            # Use hits as grounded context
            context_snippets = [
                {
                    "type": h.get("type"),
                    "text": h.get("text"),
                    "citation": h.get("citation"),
                    "score": round(float(h.get("score", 0.0)), 4),
                }
                for h in hits
            ]

            prompt = (
                "You are analyzing Swiss energy reports. Answer the query using only the provided excerpts.\n"
                "Cite each claim with (doc, page). If multiple sources disagree, explain.\n"
                f"Query: {query}\n\nExcerpts:\n" +
                "\n\n".join(
                    [
                        f"- [{i+1}] ({s['citation'].get('doc')}, p{s['citation'].get('page')}) {s['text'][:800]}"
                        for i, s in enumerate(context_snippets)
                        if s.get('text')
                    ]
                )
            )

            messages = self._prepare_messages(prompt)
            response_content = await self._call_openai(messages)

            data_sources = []
            for h in hits:
                cit = h.get('citation')
                if isinstance(cit, dict):
                    doc = cit.get('doc')
                    page = cit.get('page')
                    if doc and isinstance(doc, str) and doc.strip():
                        # Accept int, str, or convertible page
                        if page is not None and (isinstance(page, (int, str)) or hasattr(page, '__str__')):
                            try:
                                page_str = str(page)
                                data_sources.append(f"{doc}#p{page_str}")
                            except Exception:
                                print(f"Warning: Could not format page in citation: {cit}")
                        else:
                            print(f"Warning: Malformed page in citation: {cit}")
                    else:
                        print(f"Warning: Malformed doc in citation: {cit}")
                else:
                    print(f"Warning: Citation is not a dict: {cit}")
                # Attach figure thumbnail if available
                if h.get('type') == 'figure_captions':
                    img_path = (h.get('metadata') or {}).get('image_path')
                    # Validate image path
                    if isinstance(img_path, str) and img_path.strip():
                        abs_img_path = os.path.abspath(img_path)
                        # Define allowed root directories (customize as needed)
                        allowed_roots = [os.path.abspath('data/ingest/figures'), os.path.abspath('data/chroma'), os.path.abspath('data/reports')]
                        if any(abs_img_path.startswith(root) for root in allowed_roots):
                            if os.path.exists(abs_img_path) and os.path.isfile(abs_img_path):
                                data_sources.append(abs_img_path)
                            else:
                                print(f"Warning: Image path does not exist or is not a file: {img_path}")
                        else:
                            print(f"Warning: Image path not in allowed directories: {img_path}")
                    else:
                        # No image path available; skip without warning to reduce noise
                        pass

            return AgentResponse(
                content=response_content,
                confidence=min(0.85, 0.5 + 0.05 * len(hits)),
                data_sources=data_sources,
                reasoning=f"Used {len(hits)} retrieval hits as grounding context",
                suggestions=[
                    "Ask to view specific pages for verification",
                    "Request underlying datasets or methodology",
                ],
                    retrieval_method="vector_index"
            )

        # Fallback: identify relevant documents via heuristics
        # Identify relevant documents
        relevant_docs = self._identify_relevant_documents(query)
        
        if not relevant_docs:
            return AgentResponse(
                content="I couldn't find relevant documents for your query. The available reports focus on Swiss Energy Perspectives 2050+ scenarios, technical methodologies, and policy analysis.",
                confidence=0.2,
                suggestions=["Ask about specific topics like methodology, scenarios, or sector analysis"],
                retrieval_method="direct_search"
            )
        
        # Extract relevant information from documents
        extracted_info = await self._extract_information(query, relevant_docs)
        
        # Generate response
        response = await self._generate_document_response(query, extracted_info, relevant_docs)
        
        return response
    
    def _identify_relevant_documents(self, query: str) -> List[Dict[str, Any]]:
        """Identify documents relevant to the query."""
        query_lower = query.lower()
        relevant_docs = []
        
        # Keywords for document relevance
        keyword_mappings = {
            'methodology': ['technischer', 'technical', 'method'],
            'summary': ['kurzbericht', 'summary', 'overview'],
            'facts': ['faktenblatt', 'fact', 'data'],
            'biomass': ['biomasse', 'biomass'],
            'winter': ['winter', 'winterstrom'],
            'ccs': ['ccs', 'net'],
            'stakeholder': ['stellungnahmen', 'begleitgruppe'],
            'economic': ['vwl', 'economic', 'ecoplan']
        }
        
        for doc_name, doc_info in self.document_catalog.items():
            relevance_score = 0
            
            # Check filename relevance
            for query_keyword, doc_patterns in keyword_mappings.items():
                if query_keyword in query_lower:
                    for pattern in doc_patterns:
                        if pattern in doc_name.lower():
                            relevance_score += 3
            
            # Check document type relevance
            if 'technical' in query_lower and doc_info['type'] == 'Technical Report':
                relevance_score += 2
            elif 'summary' in query_lower and doc_info['type'] == 'Executive Summary':
                relevance_score += 2
            
            # General keyword search in filename
            query_words = query_lower.split()
            for word in query_words:
                if len(word) > 3 and word in doc_name.lower():
                    relevance_score += 1
            
            if relevance_score > 0:
                relevant_docs.append({
                    'filename': doc_name,
                    'info': doc_info,
                    'relevance': relevance_score
                })
        
        # Sort by relevance and limit results
        relevant_docs.sort(key=lambda x: x['relevance'], reverse=True)
        return relevant_docs[:3]  # Top 3 most relevant documents
    
    async def _extract_information(self, query: str, relevant_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract relevant information from documents."""
        extracted_info = {}
        
        for doc_info in relevant_docs:
            filename = doc_info['filename']
            
            try:
                # Search for query-relevant text in the document
                search_results = self.pdf_processor.search_text(query, filename)
                
                if search_results:
                    extracted_info[filename] = {
                        'type': doc_info['info']['type'],
                        'language': doc_info['info']['language'],
                        'matches': search_results.get(filename, [])[:3],  # Top 3 matches
                        'relevance': doc_info['relevance']
                    }
                else:
                    # If no direct matches, get document overview
                    text_preview = self.pdf_processor.extract_text(filename)[:1000]
                    extracted_info[filename] = {
                        'type': doc_info['info']['type'],
                        'language': doc_info['info']['language'],
                        'preview': text_preview,
                        'relevance': doc_info['relevance']
                    }
                    
            except Exception as e:
                print(f"Error extracting from {filename}: {e}")
                continue
        
        return extracted_info
    
    async def _generate_document_response(self, query: str, extracted_info: Dict[str, Any], 
                                         relevant_docs: List[Dict[str, Any]]) -> AgentResponse:
        """Generate response based on document analysis."""
        
        # Prepare information for LLM processing
        info_summary = {}
        for doc_name, info in extracted_info.items():
            info_summary[doc_name] = {
                'type': info['type'],
                'language': info['language'],
                'content_excerpt': info.get('matches', [])[:2] or [info.get('preview', '')[:500]]
            }
        
        response_prompt = f"""
        Based on the Swiss Energy Scenarios documents, answer the query: "{query}"
        
        Available Document Information:
        {json.dumps(info_summary, indent=2, ensure_ascii=False)}
        
        Provide a comprehensive response that:
        1. Directly answers the user's question
        2. Cites specific documents and sources
        3. Explains technical concepts clearly
        4. Distinguishes between facts, assumptions, and projections
        5. Notes any limitations or uncertainties
        6. Relates findings to Swiss energy policy context
        7. Suggests related information or documents
        
        Important: Always cite your sources with document names and indicate the type of document.
        If information is in German, provide English explanation while noting the original source.
        """
        
        messages = self._prepare_messages(response_prompt)
        response_content = await self._call_openai(messages)
        
        # Calculate confidence
        confidence = self._calculate_document_confidence(extracted_info, relevant_docs)
        
        # Extract data sources
        data_sources = [doc['filename'] for doc in relevant_docs]
        
        # Generate suggestions
        suggestions = self._generate_document_suggestions(query, relevant_docs)
        
        return AgentResponse(
            content=response_content,
            confidence=confidence,
            data_sources=data_sources,
            reasoning=f"Analyzed {len(relevant_docs)} relevant documents",
            suggestions=suggestions
        )
    
    def _calculate_document_confidence(self, extracted_info: Dict[str, Any], 
                                     relevant_docs: List[Dict[str, Any]]) -> float:
        """Calculate confidence in document analysis."""
        base_confidence = 0.3
        
        # Number of relevant documents
        if len(relevant_docs) >= 3:
            base_confidence += 0.3
        elif len(relevant_docs) >= 2:
            base_confidence += 0.2
        elif len(relevant_docs) >= 1:
            base_confidence += 0.1
        
        # Quality of matches
        for doc_info in extracted_info.values():
            if 'matches' in doc_info and doc_info['matches']:
                base_confidence += 0.1
            if doc_info.get('relevance', 0) >= 3:
                base_confidence += 0.1
        
        # Document type diversity
        doc_types = set(doc['info']['type'] for doc in relevant_docs)
        if len(doc_types) > 1:
            base_confidence += 0.1
        
        return min(base_confidence, 0.9)
    
    def _generate_document_suggestions(self, query: str, relevant_docs: List[Dict[str, Any]]) -> List[str]:
        """Generate suggestions for document exploration."""
        suggestions = []
        
        # Document type suggestions
        doc_types = [doc['info']['type'] for doc in relevant_docs]
        
        if 'Technical Report' not in doc_types:
            suggestions.append("Check the technical report for detailed methodology")
        
        if 'Executive Summary' not in doc_types:
            suggestions.append("Review the executive summary for key policy insights")
        
        # Topic-specific suggestions
        if 'methodology' not in query.lower():
            suggestions.append("Explore the methodology and assumptions used")
        
        if 'scenario' not in query.lower():
            suggestions.append("Compare findings across different scenarios")
        
        return suggestions[:3]
