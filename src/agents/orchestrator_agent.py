import asyncio
from typing import Dict, Any, List, Optional
import re
from agents.base_agent import BaseAgent, AgentResponse

class OrchestratorAgent(BaseAgent):
    def __init__(self, openai_api_key: str, agents_registry: Dict[str, BaseAgent] = None):
        self.agents_registry = agents_registry or {}
        super().__init__(
            name="Orchestrator",
            description="Central coordinator that routes queries to appropriate specialist agents",
            openai_api_key=openai_api_key
        )
        
    def register_agent(self, agent: BaseAgent):
        """Register a specialist agent."""
        self.agents_registry[agent.name] = agent
        
    def _build_system_prompt(self) -> str:
        agent_descriptions = "\n".join([
            f"- {name}: {agent.description}"
            for name, agent in self.agents_registry.items()
        ])
        
        return f"""You are the Orchestrator Agent for the Swiss Energy Scenarios Decipher System.

Your role is to:
1. Analyze user queries about Swiss energy scenarios and data
2. Determine which specialist agent(s) can best answer the query
3. Route queries to appropriate agents
4. Synthesize responses from multiple agents when needed
5. Provide clear, accessible answers to different user types (citizens, journalists, students, policymakers)

Available specialist agents:
{agent_descriptions}

Query Types and Routing Logic:
- Data questions (statistics, trends, comparisons) → Data Interpreter Agent
- Scenario comparisons and analysis → Scenario Analyst Agent  
- Document/report questions → Document Intelligence Agent
- Policy implications and context → Policy Context Agent
- Multiple aspects → Route to multiple agents

Response Format:
Always provide:
1. Direct answer to the user's question
2. Supporting data/evidence
3. Confidence level
4. Suggested follow-up questions

Adapt your communication style based on user type:
- Citizens: Simple, practical explanations
- Journalists: Facts with context and story angles
- Students: Educational content with explanations
- Policymakers: Comprehensive analysis with implications
"""
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Process query and route to appropriate agents."""
        # Analyze query to determine routing
        routing_decision = await self._analyze_query_routing(query, context)
        
        # Route to appropriate agents
        agent_responses = await self._route_to_agents(query, routing_decision, context)
        
        # Synthesize final response
        final_response = await self._synthesize_response(query, agent_responses, routing_decision)
        
        return final_response
    
    async def _analyze_query_routing(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze query to determine which agents to route to."""
        analysis_prompt = f"""
        Analyze this query about Swiss energy scenarios and determine which agents should handle it:
        
        Query: "{query}"
        
        Available agents:
        - DataInterpreter: Handles data analysis, statistics, trends from CSV files
        - ScenarioAnalyst: Compares scenarios, analyzes pathways and variants
        - DocumentIntelligence: Processes PDF reports and documents
        - PolicyContext: Provides policy implications and regulatory context
        
        Respond with JSON format:
        {{
            "primary_agents": ["agent1", "agent2"],
            "query_type": "data_analysis|scenario_comparison|document_search|policy_question|complex",
            "complexity": "simple|medium|complex",
            "user_type": "citizen|journalist|student|policymaker",
            "data_needs": ["csv_data", "pdf_reports", "scenario_comparison", "policy_context"]
        }}
        """
        
        messages = self._prepare_messages(analysis_prompt, context)
        response_text = await self._call_openai(messages)
        
        try:
            import json
            routing_info = json.loads(response_text)
        except:
            # Fallback routing
            routing_info = {
                "primary_agents": ["DataInterpreter"],
                "query_type": "data_analysis",
                "complexity": "medium",
                "user_type": "citizen",
                "data_needs": ["csv_data"]
            }
            
        return routing_info
    
    async def _route_to_agents(self, query: str, routing_decision: Dict[str, Any], 
                              context: Optional[Dict[str, Any]] = None) -> Dict[str, AgentResponse]:
        """Route query to appropriate agents in parallel."""
        agent_responses = {}
        tasks = []
        
        for agent_name in routing_decision.get("primary_agents", []):
            if agent_name in self.agents_registry:
                agent = self.agents_registry[agent_name]
                task = agent.process_query(query, context)
                tasks.append((agent_name, task))
        
        # Execute agent queries in parallel
        if tasks:
            results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            
            for i, (agent_name, _) in enumerate(tasks):
                result = results[i]
                if isinstance(result, Exception):
                    agent_responses[agent_name] = AgentResponse(
                        content=f"Error in {agent_name}: {str(result)}",
                        confidence=0.0,
                        data_sources=[],
                        reasoning=f"Agent {agent_name} encountered an error"
                    )
                else:
                    agent_responses[agent_name] = result
        
        return agent_responses
    
    async def _synthesize_response(self, query: str, agent_responses: Dict[str, AgentResponse], 
                                  routing_decision: Dict[str, Any]) -> AgentResponse:
        """Synthesize responses from multiple agents into coherent answer."""
        if not agent_responses:
            return AgentResponse(
                content="I'm sorry, I couldn't process your query. Please try rephrasing it.",
                confidence=0.1,
                data_sources=[],
                suggestions=["Try asking about specific energy data or scenarios"]
            )
        
        # If only one agent responded, return its response with orchestrator context
        if len(agent_responses) == 1:
            agent_name, response = next(iter(agent_responses.items()))
            return AgentResponse(
                content=response.content,
                confidence=response.confidence,
                data_sources=response.data_sources,
                reasoning=f"Routed to {agent_name}: {response.reasoning}",
                suggestions=response.suggestions
            )
        
        # Synthesize multiple responses
        synthesis_prompt = f"""
        Synthesize these specialist responses into a coherent answer for the user query: "{query}"
        
        User type: {routing_decision.get('user_type', 'citizen')}
        Query complexity: {routing_decision.get('complexity', 'medium')}
        
        Specialist Responses:
        """
        
        for agent_name, response in agent_responses.items():
            synthesis_prompt += f"\n{agent_name}:\n{response.content}\n"
        
        synthesis_prompt += """
        
        Provide a synthesized response that:
        1. Directly answers the user's question
        2. Integrates insights from multiple specialists
        3. Maintains appropriate complexity level for the user type
        4. Includes confidence assessment
        5. Suggests relevant follow-up questions
        """
        
        messages = self._prepare_messages(synthesis_prompt)
        synthesized_content = await self._call_openai(messages)
        
        # Calculate average confidence
        avg_confidence = sum(r.confidence for r in agent_responses.values()) / len(agent_responses)
        
        # Combine data sources
        all_sources = []
        for response in agent_responses.values():
            if response.data_sources:
                all_sources.extend(response.data_sources)
        
        # Generate suggestions
        suggestions = []
        for response in agent_responses.values():
            if response.suggestions:
                suggestions.extend(response.suggestions)
        
        return AgentResponse(
            content=synthesized_content,
            confidence=avg_confidence,
            data_sources=list(set(all_sources)),
            reasoning=f"Synthesized from {', '.join(agent_responses.keys())}",
            suggestions=list(set(suggestions))[:3]  # Limit to 3 suggestions
        )