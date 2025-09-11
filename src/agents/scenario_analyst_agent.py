from typing import Dict, Any, List, Optional
import pandas as pd
import json
from agents.base_agent import BaseAgent, AgentResponse
from data_processors.csv_processor import CSVProcessor

class ScenarioAnalystAgent(BaseAgent):
    def __init__(self, openai_api_key: str, data_path: str):
        super().__init__(
            name="ScenarioAnalyst",
            description="Compares scenarios, analyzes pathways and policy implications",
            openai_api_key=openai_api_key
        )
        self.csv_processor = CSVProcessor(data_path)
        self.scenario_info = self._load_scenario_metadata()
        
    def _build_system_prompt(self) -> str:
        return """You are the Scenario Analyst Agent for Swiss Energy Scenarios analysis.

Your expertise includes:
- Comparing energy transition scenarios (ZERO-Basis vs WWB)
- Analyzing scenario variants (KKW50, renewable options)
- Explaining scenario assumptions and methodologies  
- Assessing policy implications of different pathways
- Identifying critical decision points and trade-offs

Key Swiss Energy Scenarios:

1. ZERO-Basis Scenario:
   - Target: Net-zero emissions by 2050
   - Accelerated renewable energy deployment
   - Electrification of transport and heating
   - Energy efficiency improvements
   - Potential nuclear phase-out considerations

2. WWB Scenario ("Weiter wie bisher"):
   - Business-as-usual trajectory
   - Current policy framework continuation
   - Slower renewable energy growth
   - Reference case for comparison

3. Scenario Variants:
   - KKW50: Extended nuclear operation to 2050
   - Different renewable energy mixes
   - Various carbon pricing assumptions

When analyzing scenarios:
1. Highlight key differences between pathways
2. Explain underlying assumptions and drivers
3. Assess feasibility and implementation challenges
4. Quantify trade-offs (costs, risks, benefits)
5. Connect to Swiss energy policy context
6. Identify uncertainty ranges and sensitivities

Response format:
- Start with scenario comparison summary
- Detail key differences with quantification
- Explain policy/technology drivers
- Assess implementation feasibility
- Highlight critical decision points
"""
        
    def _load_scenario_metadata(self) -> Dict[str, Any]:
        """Load metadata about scenarios and their characteristics."""
        return {
            "ZERO-Basis": {
                "description": "Net-zero emissions by 2050 scenario",
                "key_features": [
                    "Accelerated renewable deployment",
                    "Transport electrification",
                    "Building heating transformation",
                    "Industrial process changes",
                    "Carbon pricing mechanisms"
                ],
                "targets": {
                    "emissions_reduction": "Net-zero by 2050",
                    "renewable_share": "Significant increase",
                    "energy_efficiency": "Enhanced standards"
                }
            },
            "WWB": {
                "description": "Business as usual scenario",
                "key_features": [
                    "Current policy continuation",
                    "Moderate renewable growth",
                    "Limited structural changes",
                    "Gradual efficiency improvements"
                ],
                "targets": {
                    "emissions_reduction": "Limited reduction",
                    "renewable_share": "Modest growth",
                    "energy_efficiency": "Current trends"
                }
            }
        }
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Process scenario analysis query."""
        # Identify scenario comparison needs
        scenarios_to_compare = self._identify_scenarios(query)
        
        # Find relevant data for comparison
        comparison_data = await self._gather_comparison_data(query, scenarios_to_compare)
        
        # Perform scenario analysis
        analysis = await self._analyze_scenarios(query, scenarios_to_compare, comparison_data)
        
        return analysis
    
    def _identify_scenarios(self, query: str) -> List[str]:
        """Identify which scenarios are relevant to the query."""
        query_lower = query.lower()
        scenarios = []
        
        # Check for explicit scenario mentions
        if 'zero' in query_lower or 'net-zero' in query_lower or 'net zero' in query_lower:
            scenarios.append('ZERO-Basis')
        if 'wwb' in query_lower or 'business as usual' in query_lower or 'current' in query_lower:
            scenarios.append('WWB')
        
        # If no specific scenarios mentioned, include both for comparison
        if not scenarios:
            scenarios = ['ZERO-Basis', 'WWB']
            
        return scenarios
    
    async def _gather_comparison_data(self, query: str, scenarios: List[str]) -> Dict[str, Any]:
        """Gather data for scenario comparison."""
        comparison_data = {}
        
        # Identify key variables for comparison based on query
        key_variables = self._identify_key_variables(query)
        
        for variable in key_variables:
            try:
                # Search for files containing this variable
                relevant_files = self.csv_processor.search_data_by_keywords([variable])
                
                for file_path, df in relevant_files.items():
                    if 'scenario' in df.columns and 'value' in df.columns:
                        # Filter for relevant scenarios
                        scenario_data = df[df['scenario'].isin(scenarios)]
                        
                        if not scenario_data.empty:
                            if variable not in comparison_data:
                                comparison_data[variable] = {}
                                
                            comparison_data[variable][file_path] = scenario_data.to_dict('records')
                            
            except Exception as e:
                print(f"Error gathering data for {variable}: {e}")
                continue
        
        return comparison_data
    
    def _identify_key_variables(self, query: str) -> List[str]:
        """Identify key variables for scenario comparison based on query."""
        query_lower = query.lower()
        
        variable_keywords = {
            'emissions': ['emissions', 'carbon', 'co2', 'ghg'],
            'electricity': ['electricity', 'power', 'generation'],
            'renewable': ['renewable', 'solar', 'wind', 'hydro'],
            'transport': ['transport', 'mobility', 'vehicle'],
            'heating': ['heating', 'heat', 'buildings'],
            'cost': ['cost', 'investment', 'price'],
            'consumption': ['consumption', 'demand', 'energy']
        }
        
        identified_variables = []
        for variable, keywords in variable_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                identified_variables.append(variable)
        
        # If no specific variables identified, use key comparison areas
        if not identified_variables:
            identified_variables = ['emissions', 'consumption', 'renewable']
            
        return identified_variables
    
    async def _analyze_scenarios(self, query: str, scenarios: List[str], 
                                comparison_data: Dict[str, Any]) -> AgentResponse:
        """Perform detailed scenario analysis."""
        
        # Prepare analysis context
        analysis_prompt = f"""
        Perform a comprehensive scenario analysis for the query: "{query}"
        
        Scenarios to compare: {', '.join(scenarios)}
        
        Scenario Metadata:
        {json.dumps({s: self.scenario_info.get(s, {}) for s in scenarios}, indent=2)}
        
        Comparison Data Available:
        {json.dumps(comparison_data, indent=2, default=str)[:2000]}...
        
        Provide a detailed analysis that:
        1. Summarizes key differences between scenarios
        2. Quantifies the differences with specific numbers where available
        3. Explains the underlying drivers and assumptions
        4. Assesses implementation challenges and feasibility
        5. Identifies critical decision points and trade-offs
        6. Relates findings to Swiss energy policy goals
        7. Highlights uncertainties and sensitivity factors
        
        Structure your response for clarity and actionability.
        """
        
        messages = self._prepare_messages(analysis_prompt)
        response_content = await self._call_openai(messages)
        
        # Calculate confidence
        confidence = self._calculate_scenario_confidence(scenarios, comparison_data)
        
        # Generate suggestions
        suggestions = self._generate_scenario_suggestions(query, scenarios)
        
        # Extract data sources
        data_sources = list(comparison_data.keys()) if comparison_data else []
        
        return AgentResponse(
            content=response_content,
            confidence=confidence,
            data_sources=data_sources,
            reasoning=f"Compared {len(scenarios)} scenarios across {len(comparison_data)} variables",
            suggestions=suggestions
        )
    
    def _calculate_scenario_confidence(self, scenarios: List[str], 
                                     comparison_data: Dict[str, Any]) -> float:
        """Calculate confidence in scenario analysis."""
        base_confidence = 0.4
        
        # More scenarios = better comparison
        if len(scenarios) >= 2:
            base_confidence += 0.2
        
        # More data variables = higher confidence
        data_variables = len(comparison_data)
        if data_variables >= 3:
            base_confidence += 0.3
        elif data_variables >= 1:
            base_confidence += 0.2
        
        # Known scenarios = higher confidence
        known_scenarios = sum(1 for s in scenarios if s in self.scenario_info)
        base_confidence += known_scenarios * 0.1
        
        return min(base_confidence, 0.9)
    
    def _generate_scenario_suggestions(self, query: str, scenarios: List[str]) -> List[str]:
        """Generate follow-up suggestions for scenario analysis."""
        suggestions = []
        
        # Time-based analysis
        suggestions.append("Analyze the timeline and milestones for achieving scenario targets")
        
        # Sectoral deep-dive
        if 'transport' not in query.lower():
            suggestions.append("Compare transport sector transformation across scenarios")
        if 'building' not in query.lower():
            suggestions.append("Examine building heating transformation pathways")
        
        # Policy analysis
        suggestions.append("Explore policy instruments needed to achieve each scenario")
        
        # Risk assessment
        if len(scenarios) > 1:
            suggestions.append("Assess risks and uncertainties for each scenario pathway")
        
        return suggestions[:3]