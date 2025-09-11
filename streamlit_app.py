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

from utils.config import config
from agents.orchestrator_agent import OrchestratorAgent
from agents.data_interpreter_agent import DataInterpreterAgent
from agents.scenario_analyst_agent import ScenarioAnalystAgent
from agents.document_intelligence_agent import DocumentIntelligenceAgent
from agents.policy_context_agent import PolicyContextAgent

# Configure Streamlit page
st.set_page_config(
    page_title="Swiss Energy Scenarios Decipher",
    page_icon="🇨🇭",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def initialize_agents():
    """Initialize all agents - cached for performance."""
    config.validate()
    
    # Initialize specialist agents
    data_interpreter = DataInterpreterAgent(config.openai_api_key, config.data_path)
    scenario_analyst = ScenarioAnalystAgent(config.openai_api_key, config.data_path)
    document_intelligence = DocumentIntelligenceAgent(config.openai_api_key, config.reports_path)
    policy_context = PolicyContextAgent(config.openai_api_key)
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent(config.openai_api_key)
    orchestrator.register_agent(data_interpreter)
    orchestrator.register_agent(scenario_analyst)
    orchestrator.register_agent(document_intelligence)
    orchestrator.register_agent(policy_context)
    
    return orchestrator

def main():
    """Main Streamlit application."""
    
    # Header
    st.title("🇨🇭 Swiss Energy Scenarios Decipher System")
    st.markdown("*Making Swiss energy transition data accessible to everyone*")
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 User Profile")
        user_type = st.selectbox(
            "Who are you?",
            ["citizen", "journalist", "student", "policymaker"],
            index=0,
            help="This helps us tailor our responses to your needs"
        )
        
        st.header("🤖 Available Agents")
        st.markdown("""
        - **📊 Data Interpreter**: Statistics & trends
        - **🔮 Scenario Analyst**: Compare pathways  
        - **📄 Document Intelligence**: Technical reports
        - **🏛️ Policy Context**: Regulations & implementation
        """)
        
        st.header("💡 Example Queries")
        example_queries = [
            "What are Switzerland's CO2 emissions in 2030?",
            "Compare ZERO vs WWB scenarios",
            "How does transport electrification progress?",
            "What policies support renewable energy?",
            "Explain the methodology used in scenarios"
        ]
        
        selected_example = st.selectbox(
            "Try an example:",
            [""] + example_queries,
            index=0
        )
        
        if selected_example and st.button("Use Example"):
            st.session_state.query_input = selected_example
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Ask Your Question")
        
        # Query input
        query = st.text_area(
            "Enter your question about Swiss energy scenarios:",
            height=100,
            key="query_input",
            placeholder="e.g., How do emissions change in the ZERO scenario?"
        )
        
        # Process button
        if st.button("🔄 Analyze", disabled=not query.strip()):
            if query.strip():
                process_query(query.strip(), user_type)
    
    with col2:
        st.header("📈 Quick Stats")
        
        # Try to show some quick statistics
        try:
            orchestrator = initialize_agents()
            data_agent = orchestrator.agents_registry.get("DataInterpreter")
            
            if data_agent:
                files = data_agent.csv_processor.get_available_files()
                
                st.metric("Data Files", 
                         len(files.get("synthesis", [])) + len(files.get("transformation", [])))
                st.metric("Synthesis Files", len(files.get("synthesis", [])))
                st.metric("Transformation Files", len(files.get("transformation", [])))
                
                # Try to get some sample data
                try:
                    sample_file = files.get("synthesis", [None])[0]
                    if sample_file:
                        df = data_agent.csv_processor.load_csv(sample_file)
                        if 'year' in df.columns:
                            year_range = f"{int(df['year'].min())} - {int(df['year'].max())}"
                            st.metric("Data Range", year_range)
                except:
                    pass
                    
        except Exception as e:
            st.error(f"Error loading system info: {str(e)}")
    
    # Conversation history
    if "conversation_history" in st.session_state and st.session_state.conversation_history:
        st.header("📝 Conversation History")
        
        for i, entry in enumerate(reversed(st.session_state.conversation_history[-5:])):  # Show last 5
            with st.expander(f"Q: {entry['query'][:80]}{'...' if len(entry['query']) > 80 else ''}"):
                st.write("**Answer:**")
                st.write(entry['response']['content'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    confidence = entry['response']['confidence']
                    st.metric("Confidence", f"{confidence:.2f}")
                
                if entry['response'].get('data_sources'):
                    with col2:
                        st.write("**Sources:**")
                        for source in entry['response']['data_sources'][:2]:
                            st.write(f"- {source}")
                
                if entry['response'].get('suggestions'):
                    with col3:
                        st.write("**Suggestions:**")
                        for suggestion in entry['response']['suggestions'][:2]:
                            st.write(f"• {suggestion}")

def process_query(query: str, user_type: str):
    """Process a user query asynchronously."""
    
    # Initialize session state
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    with st.spinner(f"🔄 Processing your query as {user_type}..."):
        try:
            # Initialize agents
            orchestrator = initialize_agents()
            
            # Prepare context
            context = {"user_type": user_type}
            
            # Process query
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                orchestrator.process_query(query, context)
            )
            loop.close()
            
            # Display results
            st.success("✅ Analysis Complete!")
            
            # Main response
            st.subheader("🎯 Answer")
            st.write(response.content)
            
            # Metadata in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                confidence_color = "green" if response.confidence > 0.7 else "orange" if response.confidence > 0.4 else "red"
                st.metric(
                    "Confidence", 
                    f"{response.confidence:.2f}",
                    help=f"Analysis confidence level"
                )
            
            with col2:
                if response.data_sources:
                    st.write("**📊 Data Sources:**")
                    for source in response.data_sources[:3]:
                        st.write(f"• {source}")
                    if len(response.data_sources) > 3:
                        st.write(f"... and {len(response.data_sources) - 3} more")
            
            with col3:
                if response.suggestions:
                    st.write("**💡 Follow-up Ideas:**")
                    for suggestion in response.suggestions:
                        if st.button(f"🔍 {suggestion[:50]}...", key=f"suggestion_{hash(suggestion)}"):
                            st.session_state.query_input = suggestion
                            st.rerun()
            
            # Analysis details
            if response.reasoning:
                with st.expander("🧠 Analysis Details"):
                    st.write(response.reasoning)
            
            # Store in history
            st.session_state.conversation_history.append({
                "query": query,
                "user_type": user_type,
                "response": {
                    "content": response.content,
                    "confidence": response.confidence,
                    "data_sources": response.data_sources or [],
                    "suggestions": response.suggestions or []
                }
            })
            
        except Exception as e:
            st.error(f"❌ Error processing query: {str(e)}")
            st.info("Please check your configuration and try again.")

if __name__ == "__main__":
    main()