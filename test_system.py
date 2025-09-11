#!/usr/bin/env python3
"""
Test script for the Swiss Energy Scenarios Decipher System
"""

import asyncio
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from utils.config import config
    from agents.orchestrator_agent import OrchestratorAgent
    from agents.data_interpreter_agent import DataInterpreterAgent
    from agents.scenario_analyst_agent import ScenarioAnalystAgent
    from agents.document_intelligence_agent import DocumentIntelligenceAgent
    from agents.policy_context_agent import PolicyContextAgent
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory with .venv activated")
    sys.exit(1)

async def test_configuration():
    """Test system configuration."""
    print("🔧 Testing Configuration...")
    try:
        config.validate()
        print("✅ Configuration validation passed")
        print(f"   Data path: {config.data_path}")
        print(f"   Reports path: {config.reports_path}")
        print(f"   Model: {config.model_name}")
        return True
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False

async def test_data_processors():
    """Test data processing capabilities."""
    print("\n📊 Testing Data Processors...")
    
    try:
        # Test CSV processor
        from data_processors.csv_processor import CSVProcessor
        csv_processor = CSVProcessor(config.data_path)
        
        files = csv_processor.get_available_files()
        synthesis_count = len(files.get('synthesis', []))
        transformation_count = len(files.get('transformation', []))
        
        print(f"✅ CSV Processor initialized")
        print(f"   Synthesis files: {synthesis_count}")
        print(f"   Transformation files: {transformation_count}")
        
        if synthesis_count > 0:
            # Test loading a file
            sample_file = files['synthesis'][0]
            df = csv_processor.load_csv(sample_file)
            print(f"   Sample file loaded: {sample_file} ({df.shape[0]} rows)")
        
        # Test PDF processor
        from data_processors.pdf_processor import PDFProcessor
        pdf_processor = PDFProcessor(config.reports_path)
        
        reports = pdf_processor.get_available_reports()
        print(f"✅ PDF Processor initialized")
        print(f"   Available reports: {len(reports)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data processors failed: {e}")
        return False

async def test_agents():
    """Test agent initialization and basic capabilities."""
    print("\n🤖 Testing Agents...")
    
    try:
        # Initialize agents
        data_interpreter = DataInterpreterAgent(config.openai_api_key, config.data_path)
        scenario_analyst = ScenarioAnalystAgent(config.openai_api_key, config.data_path)
        document_intelligence = DocumentIntelligenceAgent(config.openai_api_key, config.reports_path)
        policy_context = PolicyContextAgent(config.openai_api_key)
        
        print("✅ All specialist agents initialized")
        
        # Initialize orchestrator
        orchestrator = OrchestratorAgent(config.openai_api_key)
        orchestrator.register_agent(data_interpreter)
        orchestrator.register_agent(scenario_analyst)
        orchestrator.register_agent(document_intelligence)
        orchestrator.register_agent(policy_context)
        
        print("✅ Orchestrator initialized and agents registered")
        print(f"   Registered agents: {list(orchestrator.agents_registry.keys())}")
        
        return orchestrator
        
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return None

async def test_simple_query(orchestrator):
    """Test a simple query through the system."""
    print("\n💬 Testing Simple Query...")
    
    if not orchestrator:
        print("❌ Cannot test query - orchestrator not available")
        return False
    
    try:
        # Test query
        query = "What data is available about Swiss energy scenarios?"
        print(f"   Query: {query}")
        
        context = {"user_type": "citizen"}
        response = await orchestrator.process_query(query, context)
        
        print("✅ Query processed successfully")
        print(f"   Response length: {len(response.content)} characters")
        print(f"   Confidence: {response.confidence:.2f}")
        print(f"   Data sources: {len(response.data_sources or [])}")
        print(f"   Suggestions: {len(response.suggestions or [])}")
        
        # Show first 200 characters of response
        preview = response.content[:200] + "..." if len(response.content) > 200 else response.content
        print(f"   Preview: {preview}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("=" * 80)
    print("🇨🇭 SWISS ENERGY SCENARIOS DECIPHER SYSTEM - TESTING")
    print("=" * 80)
    
    # Run tests
    config_ok = await test_configuration()
    if not config_ok:
        print("\n❌ Configuration test failed - stopping tests")
        return
    
    data_ok = await test_data_processors()
    if not data_ok:
        print("\n⚠️  Data processor issues detected")
    
    orchestrator = await test_agents()
    if not orchestrator:
        print("\n❌ Agent initialization failed - skipping query test")
    else:
        await test_simple_query(orchestrator)
    
    print("\n" + "=" * 80)
    print("🏁 TESTING COMPLETE")
    
    if config_ok and orchestrator:
        print("✅ System is ready for use!")
        print("\nTo start the application:")
        print("   CLI: python main.py")
        print("   Web: streamlit run streamlit_app.py")
    else:
        print("❌ System has issues that need to be resolved")
    
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())