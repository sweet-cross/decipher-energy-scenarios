from typing import Dict, Any, List, Optional
import json
from agents.base_agent import BaseAgent, AgentResponse

class PolicyContextAgent(BaseAgent):
    def __init__(self, openai_api_key: str):
        super().__init__(
            name="PolicyContext",
            description="Provides policy implications and regulatory context for energy scenarios",
            openai_api_key=openai_api_key
        )
        self.policy_knowledge = self._load_policy_knowledge()
        
    def _build_system_prompt(self) -> str:
        return """You are the Policy Context Agent for Swiss Energy Scenarios analysis.

Your expertise includes:
- Swiss energy policy framework and legislation
- Climate policy commitments (Paris Agreement, Net-Zero 2050)
- Energy transition governance and implementation
- Regulatory instruments and market mechanisms
- Stakeholder impacts and social acceptance
- International energy cooperation and dependencies

Key Swiss Energy Policy Context:

1. Constitutional and Legal Framework:
   - Energy Strategy 2050 (constitutional amendment 2017)
   - CO2 Act and climate legislation
   - Federal Energy Act (EnG) and ordinances
   - Cantonal energy planning competencies

2. Climate Commitments:
   - Paris Agreement implementation
   - Net-zero emissions target by 2050
   - Interim reduction targets (2030: -50% vs 1990)
   - Long-term climate strategy (LTS)

3. Energy Transition Pillars:
   - Nuclear phase-out (referendum decision)
   - Renewable energy expansion targets
   - Energy efficiency improvements
   - Grid infrastructure modernization
   - Sector coupling (heating, transport, electricity)

4. Policy Instruments:
   - CO2 levy and emissions trading
   - Renewable energy incentives (KEV/EVS)
   - Building energy standards (MuKEn)
   - Transport electrification support
   - R&D funding and innovation programs

5. Governance Structure:
   - Federal-cantonal coordination
   - Energy dialogue with stakeholders
   - Regular monitoring and reporting
   - International cooperation frameworks

When providing policy context:
1. Connect scenarios to specific policy measures
2. Explain implementation pathways and timelines
3. Assess political feasibility and barriers
4. Identify key decision points and governance needs
5. Quantify policy impacts where possible
6. Consider distributional effects and social acceptance
7. Relate to international best practices and commitments

Response format:
- Lead with policy implications summary
- Detail relevant regulations and instruments
- Assess implementation challenges
- Identify stakeholder impacts
- Suggest policy recommendations
- Note uncertainties and political risks
"""
        
    def _load_policy_knowledge(self) -> Dict[str, Any]:
        """Load structured policy knowledge base."""
        return {
            "key_policies": {
                "Energy_Strategy_2050": {
                    "description": "Constitutional framework for energy transition",
                    "key_targets": [
                        "Nuclear phase-out by ~2034",
                        "Renewable electricity: 11.4 TWh by 2035", 
                        "Energy efficiency: -43% per capita by 2035"
                    ],
                    "instruments": [
                        "Investment grants for renewables",
                        "Grid surcharge financing",
                        "Building efficiency standards",
                        "R&D support programs"
                    ]
                },
                "CO2_Act": {
                    "description": "Climate policy framework",
                    "key_targets": [
                        "Emissions reduction: -50% by 2030 (vs 1990)",
                        "Net-zero by 2050",
                        "Sectoral targets for transport, buildings, industry"
                    ],
                    "instruments": [
                        "CO2 levy on heating fuels",
                        "Emissions trading for large emitters", 
                        "Fuel importers' compensation duty",
                        "Climate fund for mitigation measures"
                    ]
                }
            },
            "governance": {
                "federal_level": [
                    "SFOE: Energy policy coordination",
                    "FOEN: Climate policy implementation", 
                    "SECO: Economic impact assessment"
                ],
                "cantonal_level": [
                    "Energy planning and zoning",
                    "Building codes and permits",
                    "Spatial planning coordination"
                ],
                "stakeholders": [
                    "Energy suppliers and grid operators",
                    "Industry associations", 
                    "Environmental NGOs",
                    "Consumer organizations"
                ]
            },
            "implementation_challenges": [
                "Grid expansion and acceptance",
                "Renewable energy siting conflicts", 
                "Energy storage and flexibility needs",
                "Social acceptance and cost distribution",
                "Skills and workforce transition",
                "International coordination needs"
            ]
        }
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Process policy context query."""
        # Identify policy areas relevant to the query
        relevant_policy_areas = self._identify_policy_areas(query)
        
        # Analyze policy implications
        policy_analysis = await self._analyze_policy_implications(query, relevant_policy_areas, context)
        
        return policy_analysis
    
    def _identify_policy_areas(self, query: str) -> List[str]:
        """Identify relevant policy areas based on the query."""
        query_lower = query.lower()
        policy_areas = []
        
        # Policy area keywords
        area_keywords = {
            'climate_targets': ['emission', 'climate', 'net-zero', 'co2', 'target'],
            'energy_transition': ['renewable', 'transition', 'energy strategy', 'nuclear'],
            'transport_policy': ['transport', 'mobility', 'vehicle', 'electrification'],
            'building_policy': ['building', 'heating', 'efficiency', 'renovation'],
            'economic_instruments': ['cost', 'price', 'tax', 'levy', 'incentive', 'funding'],
            'governance': ['federal', 'cantonal', 'regulation', 'law', 'implementation'],
            'international': ['eu', 'cooperation', 'trade', 'agreement', 'import']
        }
        
        for area, keywords in area_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                policy_areas.append(area)
        
        # If no specific areas identified, include key areas
        if not policy_areas:
            policy_areas = ['climate_targets', 'energy_transition']
            
        return policy_areas
    
    async def _analyze_policy_implications(self, query: str, policy_areas: List[str], 
                                          context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Analyze policy implications for the query."""
        
        # Prepare policy context information
        relevant_policies = {}
        for area in policy_areas:
            relevant_policies[area] = self._get_policy_info(area)
        
        analysis_prompt = f"""
        Analyze the policy implications for the query: "{query}"
        
        Relevant Policy Areas: {', '.join(policy_areas)}
        
        Swiss Policy Context:
        {json.dumps(self.policy_knowledge, indent=2)}
        
        Query Context (if provided):
        {json.dumps(context, indent=2) if context else "No additional context provided"}
        
        Provide a comprehensive policy analysis that:
        1. Identifies key policy implications of the query/scenario
        2. Explains relevant Swiss legal and regulatory framework
        3. Assesses implementation pathways and requirements
        4. Identifies policy instruments needed or available
        5. Evaluates political feasibility and potential barriers
        6. Considers stakeholder impacts and acceptance issues
        7. Relates to international commitments and cooperation
        8. Suggests policy recommendations or next steps
        
        Focus on actionable insights for policy makers and implementation challenges.
        """
        
        messages = self._prepare_messages(analysis_prompt)
        response_content = await self._call_openai(messages)
        
        # Calculate confidence
        confidence = self._calculate_policy_confidence(policy_areas, context)
        
        # Generate suggestions
        suggestions = self._generate_policy_suggestions(query, policy_areas)
        
        return AgentResponse(
            content=response_content,
            confidence=confidence,
            data_sources=[f"Swiss policy framework: {area}" for area in policy_areas],
            reasoning=f"Analyzed {len(policy_areas)} policy areas",
            suggestions=suggestions
        )
    
    def _get_policy_info(self, area: str) -> Dict[str, Any]:
        """Get specific policy information for an area."""
        area_mapping = {
            'climate_targets': {
                'key_policies': ['CO2_Act'],
                'targets': ['Net-zero by 2050', 'Interim targets'],
                'challenges': ['Emissions monitoring', 'Sectoral implementation']
            },
            'energy_transition': {
                'key_policies': ['Energy_Strategy_2050'],
                'targets': ['Renewable expansion', 'Nuclear phase-out'],
                'challenges': ['Grid integration', 'Storage needs']
            },
            'transport_policy': {
                'instruments': ['CO2 fleet standards', 'Fuel taxation', 'EV incentives'],
                'challenges': ['Charging infrastructure', 'Modal shift']
            },
            'building_policy': {
                'instruments': ['MuKEn standards', 'Building program', 'Heat pump subsidies'],
                'challenges': ['Renovation rates', 'Heat pump deployment']
            },
            'economic_instruments': {
                'current': ['CO2 levy', 'Grid surcharge', 'Investment grants'],
                'potential': ['Carbon pricing extension', 'Green bonds']
            },
            'governance': {
                'coordination': ['Federal-cantonal', 'Cross-sectoral'],
                'challenges': ['Competency conflicts', 'Implementation gaps']
            }
        }
        
        return area_mapping.get(area, {})
    
    def _calculate_policy_confidence(self, policy_areas: List[str], 
                                   context: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence in policy analysis."""
        base_confidence = 0.6  # Higher base for policy knowledge
        
        # Known policy areas increase confidence
        known_areas = sum(1 for area in policy_areas if area in [
            'climate_targets', 'energy_transition', 'transport_policy', 
            'building_policy', 'economic_instruments', 'governance'
        ])
        base_confidence += known_areas * 0.05
        
        # Additional context helps
        if context:
            base_confidence += 0.1
            
        return min(base_confidence, 0.9)
    
    def _generate_policy_suggestions(self, query: str, policy_areas: List[str]) -> List[str]:
        """Generate policy-related suggestions."""
        suggestions = []
        
        # Implementation focus
        suggestions.append("Explore specific implementation pathways and timelines")
        
        # Stakeholder analysis
        if 'governance' not in policy_areas:
            suggestions.append("Assess stakeholder impacts and coordination needs")
        
        # Economic analysis
        if 'economic_instruments' not in policy_areas:
            suggestions.append("Examine economic instruments and financing mechanisms")
        
        # International dimension
        suggestions.append("Consider international cooperation and EU policy alignment")
        
        # Sectoral policies
        if 'transport_policy' not in policy_areas and 'transport' in query.lower():
            suggestions.append("Analyze transport policy instruments and regulations")
        
        return suggestions[:3]