import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from src.retrieval.retriever import Retriever
import os
import json
from agents.base_agent import BaseAgent, AgentResponse
from data_processors.csv_processor import CSVProcessor
from retrieval.retriever import Retriever
from data_processors.dataset_catalog import DatasetCatalog

class DataInterpreterAgent(BaseAgent):
    def __init__(self, openai_api_key: str, data_path: str, retriever: Optional[Retriever] = None):
        super().__init__(
            name="DataInterpreter",
            description="Analyzes energy data from CSV files, provides statistics and trends",
            openai_api_key=openai_api_key
        )
        self.csv_processor = CSVProcessor(data_path)
        self.retriever = retriever or Retriever(persist_dir="data/chroma")
        self.dataset_catalog = DatasetCatalog(data_path)
        self.data_catalog = self._build_data_catalog()
        
    def _build_system_prompt(self) -> str:
        return """You are the Data Interpreter Agent for Swiss Energy Scenarios analysis.

Your expertise includes:
- Analyzing energy consumption, generation, and emission data
- Comparing data across different scenarios (ZERO-Basis, WWB, etc.)
- Extracting trends and patterns from time series data
- Providing statistical analysis and forecasts
- Explaining data in context of Swiss energy transition

Data Categories Available:
1. SYNTHESIS DATA (80+ files):
   - Demographics & Economics
   - Emissions (GHG, CO2, CH4, N2O, F-gases)
   - Energy Consumption (by fuel, sector, purpose)
   - Electricity (consumption, generation, prices)
   - Renewables, Biomass, District Heating
   - Transport, Buildings, Industry, Agriculture
   - Power-to-X and Heat Pumps
   - Cost Analysis

2. TRANSFORMATION DATA:
   - Electricity generation by technology
   - Capacity by renewable technology  
   - Seasonal generation patterns
   - District heating and Power-to-X

Key Scenarios & Variants:
- ZERO-Basis: Base scenario for net-zero by 2050
- WWB: "Weiter wie bisher" (Business as usual)
- Variants: KKW50 (nuclear), renewable energy options

When analyzing data:
1. Always specify data source and time frame
2. Compare scenarios when relevant
3. Identify trends and inflection points
4. Explain methodology and assumptions
5. Quantify uncertainty where applicable
6. Relate findings to Swiss energy policy goals

Response format:
- Lead with key finding/answer
- Provide supporting statistics
- Include data source and confidence level
- Suggest related data points for deeper analysis
"""
    
    def _build_data_catalog(self) -> Dict[str, Dict[str, Any]]:
        """Build catalog of available data files."""
        catalog = {}
        
        try:
            files = self.csv_processor.get_available_files()
            
            for category in ['synthesis', 'transformation']:
                catalog[category] = {}
                for filename in files.get(category, []):
                    try:
                        summary = self.csv_processor.get_data_summary(filename, category)
                        catalog[category][filename] = summary
                    except Exception as e:
                        print(f"Error cataloging {filename}: {e}")
                        
        except Exception as e:
            print(f"Error building data catalog: {e}")
            
        return catalog
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Process data analysis query."""
        # Try semantic mapping from query -> dataset cards
        relevant_files = []
        try:
            ds_hits = self.retriever.search_datasets(query, k=5)
        except Exception as e:
            print(f"Warning: Retriever search failed: {e}")
            ds_hits = []

        if ds_hits:
            # Build file descriptors from dataset_id
            listed = self.dataset_catalog.list_csvs()
            for h in ds_hits:
                did = h.get("dataset_id")
                cat = "synthesis" if did in listed.get("synthesis", []) else (
                    "transformation" if did in listed.get("transformation", []) else None
                )
                if cat:
                    relevant_files.append({
                        'filename': did,
                        'category': cat,
                        'relevance': h.get('score', 0),
                        'summary': self.csv_processor.get_data_summary(did, cat)
                    })

        if not relevant_files:
            # Fallback heuristic
            relevant_files = self._identify_relevant_data(query)
        
        if not relevant_files:
            return AgentResponse(
                content="I couldn't find relevant data for your query. Please be more specific about the energy aspect you're interested in.",
                confidence=0.2,
                suggestions=["Try asking about specific sectors like transport, buildings, or electricity generation"]
            )
        
        # Extract and analyze data
        analysis_results = await self._analyze_data(query, relevant_files, context)
        
        # Generate response
        response = await self._generate_data_response(query, analysis_results, relevant_files)
        
        return response
    
    def _identify_relevant_data(self, query: str) -> List[Dict[str, str]]:
        """Identify which data files are relevant to the query."""
        query_lower = query.lower()
        relevant_files = []
        
        # Keywords mapping to file patterns
        keyword_mappings = {
            'emission': ['emissions', 'ghg', 'co2', 'ch4', 'n20'],
            'electricity': ['electricity', 'power', 'generation'],
            'renewable': ['renewable', 'solar', 'wind', 'hydro'],
            'transport': ['transport', 'mobility', 'vehicle', 'aviation'],
            'building': ['building', 'heating', 'residential'],
            'industry': ['industry', 'industrial', 'manufacturing'],
            'cost': ['cost', 'investment', 'price'],
            'consumption': ['consumption', 'demand', 'usage'],
            'biomass': ['biomass', 'wood', 'waste'],
            'heat': ['heat', 'heating', 'district_heating'],
            'demography': ['population', 'demographic', 'economic']
        }
        
        # Check each file in catalog
        for category, files in self.data_catalog.items():
            for filename, file_info in files.items():
                file_relevance = 0
                
                # Check filename relevance
                for keyword, patterns in keyword_mappings.items():
                    if keyword in query_lower:
                        for pattern in patterns:
                            if pattern in filename.lower():
                                file_relevance += 2
                
                # Check variables in file
                if 'variables' in file_info:
                    for variable in file_info['variables']:
                        for word in query_lower.split():
                            if word in variable.lower():
                                file_relevance += 1
                
                if file_relevance > 0:
                    relevant_files.append({
                        'filename': filename,
                        'category': category,
                        'relevance': file_relevance,
                        'summary': file_info
                    })
        
        # Sort by relevance and return top files
        relevant_files.sort(key=lambda x: x['relevance'], reverse=True)
        return relevant_files[:5]  # Limit to top 5 most relevant files
    
    async def _analyze_data(self, query: str, relevant_files: List[Dict[str, str]], 
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform actual data analysis on relevant files."""
        analysis_results = {
            'data_summary': {},
            'key_statistics': {},
            'trends': {},
            'comparisons': {}
        }
        
        for file_info in relevant_files:
            filename = file_info['filename']
            category = file_info['category']
            
            try:
                df = self.csv_processor.load_csv(filename, category)
                
                # Basic statistics
                if 'year' in df.columns:
                    y = pd.to_numeric(df['year'], errors='coerce').dropna()
                    years = [int(y.min()), int(y.max())] if not y.empty else None
                else:
                    years = None
                analysis_results['data_summary'][filename] = {
                    'shape': df.shape,
                    'years': years,
                    'scenarios': df['scenario'].dropna().unique().tolist() if 'scenario' in df.columns else [],
                    'variables': df['variable'].dropna().unique().tolist() if 'variable' in df.columns else []
                }
                
                # Calculate key statistics
                if 'value' in df.columns and 'year' in df.columns:
                    y = pd.to_numeric(df['year'], errors='coerce')
                    v = pd.to_numeric(df['value'], errors='coerce')
                    df2 = df.copy()
                    df2['year'] = y
                    df2['value'] = v
                    df2 = df2.dropna(subset=['year', 'value'])
                    stats = {'latest_value': None, 'earliest_value': None, 'mean_value': None, 'growth_rate': None}
                    if not df2.empty:
                        y_min = df2['year'].min()
                        y_max = df2['year'].max()
                        latest_series = df2.loc[df2['year'] == y_max, 'value'].dropna()
                        earliest_series = df2.loc[df2['year'] == y_min, 'value'].dropna()
                        stats['latest_value'] = float(latest_series.iloc[0]) if not latest_series.empty else None
                        stats['earliest_value'] = float(earliest_series.iloc[0]) if not earliest_series.empty else None
                        stats['mean_value'] = float(df2['value'].mean()) if not df2['value'].dropna().empty else None
                        if stats['latest_value'] is not None and stats['earliest_value'] is not None and stats['earliest_value'] != 0:
                            years_span = y_max - y_min
                            if years_span and years_span > 0:
                                stats['growth_rate'] = ((stats['latest_value'] / stats['earliest_value']) ** (1/years_span) - 1) * 100
                    
                    analysis_results['key_statistics'][filename] = stats
                
            except Exception as e:
                print(f"Error analyzing {filename}: {e}")
                continue
        
        return analysis_results
    
    async def _generate_data_response(self, query: str, analysis_results: Dict[str, Any], 
                                     relevant_files: List[Dict[str, str]]) -> AgentResponse:
        """Generate response based on data analysis."""
        # Prepare analysis summary for LLM
        analysis_summary = json.dumps(analysis_results, indent=2, default=str)
        files_summary = json.dumps([f"{f['filename']} (relevance: {f['relevance']})" for f in relevant_files])
        
        response_prompt = f"""
        Based on the data analysis for the query: "{query}"
        
        Analysis Results:
        {analysis_summary}
        
        Data Sources Used:
        {files_summary}
        
        Provide a comprehensive data-driven response that:
        1. Directly answers the user's question with specific numbers
        2. Identifies key trends and patterns
        3. Compares scenarios where relevant
        4. Explains the significance of the findings
        5. Notes any limitations or uncertainties
        6. Suggests related data points for further exploration
        
        Format the response to be accessible but data-rich.
        """
        
        messages = self._prepare_messages(response_prompt)
        response_content = await self._call_openai(messages)
        
        # Calculate confidence based on data availability and quality
        confidence = self._calculate_confidence(analysis_results, relevant_files)
        
        # Extract data sources
        data_sources = [f"{f['category']}/{f['filename']}" for f in relevant_files]
        
        # Generate suggestions
        suggestions = self._generate_suggestions(query, relevant_files)
        
        return AgentResponse(
            content=response_content,
            confidence=confidence,
            data_sources=data_sources,
            reasoning=f"Analyzed {len(relevant_files)} relevant data files",
            suggestions=suggestions
        )
    
    def _calculate_confidence(self, analysis_results: Dict[str, Any], 
                            relevant_files: List[Dict[str, str]]) -> float:
        """Calculate confidence score based on data quality."""
        base_confidence = 0.3
        
        # More relevant files = higher confidence
        if len(relevant_files) >= 3:
            base_confidence += 0.3
        elif len(relevant_files) >= 2:
            base_confidence += 0.2
        elif len(relevant_files) >= 1:
            base_confidence += 0.1
        
        # Data quality indicators
        for filename, stats in analysis_results.get('key_statistics', {}).items():
            if stats.get('latest_value') is not None:
                base_confidence += 0.1
            if stats.get('growth_rate') is not None:
                base_confidence += 0.1
        
        return min(base_confidence, 0.9)  # Cap at 0.9
    
    def _generate_suggestions(self, query: str, relevant_files: List[Dict[str, str]]) -> List[str]:
        """Generate follow-up suggestions based on analysis."""
        suggestions = []
        
        # Suggest scenario comparisons
        scenarios_found = set()
        for file_info in relevant_files:
            scenarios = file_info.get('summary', {}).get('scenarios', [])
            scenarios_found.update(scenarios)
        
        if len(scenarios_found) > 1:
            suggestions.append("Compare the same data across different scenarios (ZERO-Basis vs WWB)")
        
        # Suggest related data exploration
        if 'electricity' in query.lower():
            suggestions.append("Explore electricity generation by technology")
            suggestions.append("Check seasonal patterns (winter vs summer)")
        
        if 'emission' in query.lower():
            suggestions.append("Analyze emissions by sector")
            suggestions.append("Look at the relationship between energy consumption and emissions")
        
        return suggestions[:3]  # Limit to 3 suggestions
