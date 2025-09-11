#!/usr/bin/env python3
"""
Demo script for the Swiss Energy Scenarios system
"""

import asyncio
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def demo():
    """Run a simple demo."""
    print("🇨🇭 Swiss Energy Scenarios Decipher - Demo")
    print("=" * 60)
    
    try:
        # Import and initialize
        from utils.config import config
        from agents.orchestrator_agent import OrchestratorAgent
        from agents.data_interpreter_agent import DataInterpreterAgent
        from agents.scenario_analyst_agent import ScenarioAnalystAgent
        from agents.document_intelligence_agent import DocumentIntelligenceAgent
        from agents.policy_context_agent import PolicyContextAgent
        
        print("✅ All imports successful!")
        
        # Validate configuration
        config.validate()
        print("✅ Configuration validated")
        
        # Initialize agents
        print("\n🤖 Initializing AI agents...")
        
        data_interpreter = DataInterpreterAgent(config.openai_api_key, config.data_path)
        scenario_analyst = ScenarioAnalystAgent(config.openai_api_key, config.data_path)
        document_intelligence = DocumentIntelligenceAgent(config.openai_api_key, config.reports_path)
        policy_context = PolicyContextAgent(config.openai_api_key)
        
        orchestrator = OrchestratorAgent(config.openai_api_key)
        orchestrator.register_agent(data_interpreter)
        orchestrator.register_agent(scenario_analyst)
        orchestrator.register_agent(document_intelligence)
        orchestrator.register_agent(policy_context)
        
        print("✅ All agents initialized and registered")
        
        # Test a simple query
        print("\n💬 Testing sample query...")
        query = "What energy data is available for Switzerland?"
        context = {"user_type": "citizen"}
        
        print(f"Query: {query}")
        print("Processing...")
        
        response = await orchestrator.process_query(query, context)
        
        print("\n✅ Response received!")
        print("=" * 60)
        print("RESPONSE:")
        print("=" * 60)
        print(response.content)
        print("=" * 60)
        print(f"Confidence: {response.confidence:.2f}")
        if response.data_sources:
            print(f"Data sources: {', '.join(response.data_sources[:3])}")
        if response.suggestions:
            print(f"Suggestions: {', '.join(response.suggestions)}")
        print("=" * 60)
        
        print("\n🎉 Demo completed successfully!")
        print("\nTo use the full system:")
        print("1. CLI: python main.py")
        print("2. Web: streamlit run streamlit_app.py")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo())