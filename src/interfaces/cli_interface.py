import asyncio
import sys
import os
from typing import Optional
import json

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils.config import config
from agents.orchestrator_agent import OrchestratorAgent
from agents.data_interpreter_agent import DataInterpreterAgent
from agents.scenario_analyst_agent import ScenarioAnalystAgent
from agents.document_intelligence_agent import DocumentIntelligenceAgent
from agents.policy_context_agent import PolicyContextAgent

class EnergyScenariosCLI:
    def __init__(self):
        config.validate()
        
        # Initialize agents
        self.data_interpreter = DataInterpreterAgent(
            config.openai_api_key, 
            config.data_path
        )
        self.scenario_analyst = ScenarioAnalystAgent(
            config.openai_api_key, 
            config.data_path
        )
        self.document_intelligence = DocumentIntelligenceAgent(
            config.openai_api_key, 
            config.reports_path
        )
        self.policy_context = PolicyContextAgent(
            config.openai_api_key
        )
        
        # Initialize orchestrator and register agents
        self.orchestrator = OrchestratorAgent(config.openai_api_key)
        self.orchestrator.register_agent(self.data_interpreter)
        self.orchestrator.register_agent(self.scenario_analyst)
        self.orchestrator.register_agent(self.document_intelligence)
        self.orchestrator.register_agent(self.policy_context)
        
        self.conversation_history = []
        
    def display_welcome(self):
        """Display welcome message and system info."""
        print("=" * 80)
        print("🇨🇭 SWISS ENERGY SCENARIOS DECIPHER SYSTEM 🇨🇭")
        print("=" * 80)
        print("Making Swiss energy transition data accessible to everyone!")
        print()
        print("Available expertise:")
        print("📊 Data Analysis - Statistics, trends, and comparisons")
        print("🔮 Scenario Analysis - Compare energy pathways") 
        print("📄 Document Intelligence - Technical reports and studies")
        print("🏛️  Policy Context - Regulations and implementation")
        print()
        print("User types supported:")
        print("👥 Citizens - Simple, practical explanations")
        print("📰 Journalists - Facts with context and story angles") 
        print("🎓 Students - Educational content with explanations")
        print("🏢 Policymakers - Comprehensive analysis with implications")
        print()
        print("Commands:")
        print("- Type your question about Swiss energy scenarios")
        print("- 'help' - Show detailed help")
        print("- 'agents' - List available agents")
        print("- 'history' - Show conversation history")
        print("- 'clear' - Clear conversation history")
        print("- 'quit' or 'exit' - Exit the system")
        print("=" * 80)
        print()
        
    def display_help(self):
        """Display detailed help information."""
        help_text = """
DETAILED HELP - Swiss Energy Scenarios Decipher System

EXAMPLE QUERIES:

📊 DATA ANALYSIS EXAMPLES:
- "What are Switzerland's CO2 emissions in 2030 under the ZERO scenario?"
- "How does electricity consumption change by sector from 2020 to 2050?"
- "Compare renewable energy growth between scenarios"
- "Show me transport energy consumption trends"

🔮 SCENARIO ANALYSIS EXAMPLES:
- "What's the difference between ZERO-Basis and WWB scenarios?"
- "How do scenarios differ in nuclear power assumptions?"
- "Compare costs between energy transition pathways"
- "What are the implications of delayed climate action?"

📄 DOCUMENT ANALYSIS EXAMPLES:
- "What methodology is used for scenario modeling?"
- "Explain the assumptions about biomass availability"
- "What do the technical reports say about winter electricity?"
- "Find information about carbon capture and storage"

🏛️  POLICY CONTEXT EXAMPLES:
- "What policies are needed to achieve net-zero by 2050?"
- "How does the CO2 Act support the energy transition?"
- "What are the implementation challenges for renewable energy?"
- "Explain Switzerland's climate commitments"

TIPS FOR BETTER RESULTS:
✅ Be specific about time periods (e.g., "by 2030", "in 2050")
✅ Mention specific sectors if relevant (transport, buildings, industry)
✅ Ask for comparisons between scenarios when appropriate
✅ Specify if you want policy implications or technical details

USER TYPES - Adapt your questions:
- Citizens: Ask practical questions about impacts and changes
- Journalists: Request facts, context, and story angles
- Students: Ask for explanations of concepts and methodology
- Policymakers: Request comprehensive analysis and recommendations
"""
        print(help_text)
        
    def display_agents(self):
        """Display available agents and their capabilities."""
        print("\n🤖 AVAILABLE SPECIALIST AGENTS:")
        print("-" * 50)
        
        agents = [
            self.data_interpreter,
            self.scenario_analyst, 
            self.document_intelligence,
            self.policy_context
        ]
        
        for agent in agents:
            capabilities = agent.get_capabilities()
            print(f"Agent: {capabilities['name']}")
            print(f"Description: {capabilities['description']}")
            print(f"Model: {capabilities['model']}")
            print()
            
    def display_history(self):
        """Display conversation history."""
        if not self.conversation_history:
            print("No conversation history yet.")
            return
            
        print("\n💬 CONVERSATION HISTORY:")
        print("-" * 50)
        
        for i, entry in enumerate(self.conversation_history, 1):
            print(f"{i}. Q: {entry['query'][:100]}{'...' if len(entry['query']) > 100 else ''}")
            print(f"   A: {entry['response']['content'][:100]}{'...' if len(entry['response']['content']) > 100 else ''}")
            print(f"   Confidence: {entry['response']['confidence']:.2f}")
            print()
            
    async def process_query(self, query: str, user_type: str = "citizen") -> None:
        """Process a user query."""
        print(f"\n🔄 Processing your query...")
        print(f"User type: {user_type.title()}")
        print("-" * 50)
        
        try:
            # Add user context
            context = {"user_type": user_type}
            
            # Process with orchestrator
            response = await self.orchestrator.process_query(query, context)
            
            # Display response
            self._display_response(response)
            
            # Store in history
            self.conversation_history.append({
                "query": query,
                "user_type": user_type,
                "response": {
                    "content": response.content,
                    "confidence": response.confidence,
                    "data_sources": response.data_sources,
                    "suggestions": response.suggestions
                }
            })
            
        except Exception as e:
            print(f"❌ Error processing query: {str(e)}")
            print("Please try rephrasing your question or contact support.")
            
    def _display_response(self, response) -> None:
        """Display the agent response in a formatted way."""
        print("✅ RESPONSE:")
        print("-" * 50)
        print(response.content)
        print()
        
        # Show confidence and reasoning
        confidence_emoji = "🟢" if response.confidence > 0.7 else "🟡" if response.confidence > 0.4 else "🔴"
        print(f"{confidence_emoji} Confidence: {response.confidence:.2f}")
        
        if response.reasoning:
            print(f"🧠 Analysis: {response.reasoning}")
        
        # Show data sources
        if response.data_sources:
            print(f"📊 Data sources: {', '.join(response.data_sources[:3])}")
            if len(response.data_sources) > 3:
                print(f"    ... and {len(response.data_sources) - 3} more")
        
        # Show suggestions
        if response.suggestions:
            print("\n💡 Follow-up suggestions:")
            for i, suggestion in enumerate(response.suggestions, 1):
                print(f"   {i}. {suggestion}")
        
        print("\n" + "=" * 80)
        
    def get_user_type(self) -> str:
        """Get user type from input."""
        print("Who are you? (helps us tailor responses)")
        print("1. Citizen - Practical, everyday impacts")
        print("2. Journalist - Facts and story angles") 
        print("3. Student - Educational explanations")
        print("4. Policymaker - Comprehensive analysis")
        print("5. Skip - Use default (citizen)")
        
        while True:
            choice = input("Select (1-5): ").strip()
            
            if choice == "1":
                return "citizen"
            elif choice == "2": 
                return "journalist"
            elif choice == "3":
                return "student"
            elif choice == "4":
                return "policymaker"
            elif choice == "5" or choice == "":
                return "citizen"
            else:
                print("Please enter 1, 2, 3, 4, or 5")
                
    async def run(self):
        """Run the main CLI interface."""
        self.display_welcome()
        
        # Get user type
        user_type = self.get_user_type()
        print(f"\n🎯 Mode: {user_type.title()}")
        print("Type your questions about Swiss energy scenarios...")
        print()
        
        while True:
            try:
                # Get user input
                query = input("💬 Your question: ").strip()
                
                if not query:
                    continue
                    
                # Handle commands
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Thank you for using the Swiss Energy Scenarios system!")
                    break
                elif query.lower() == 'help':
                    self.display_help()
                    continue
                elif query.lower() == 'agents':
                    self.display_agents()
                    continue
                elif query.lower() == 'history':
                    self.display_history()
                    continue
                elif query.lower() == 'clear':
                    self.conversation_history = []
                    print("🗑️  Conversation history cleared.")
                    continue
                elif query.lower() == 'user':
                    user_type = self.get_user_type()
                    print(f"🎯 Mode changed to: {user_type.title()}")
                    continue
                    
                # Process regular query
                await self.process_query(query, user_type)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {str(e)}")
                print("Please try again or type 'quit' to exit.")

if __name__ == "__main__":
    cli = EnergyScenariosCLI()
    asyncio.run(cli.run())