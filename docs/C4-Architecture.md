# 🇨🇭 Swiss Energy Scenarios Decipher System - C4 Architecture Documentation

## Overview

The Swiss Energy Scenarios Decipher System is a multiagent AI application that transforms complex energy scenario data into accessible insights for citizens, journalists, students, and policymakers.

---

## Level 1: System Context Diagram

```mermaid
C4Context
    title System Context - Swiss Energy Scenarios Decipher System

    Person(citizen, "Citizens", "General public seeking energy information")
    Person(journalist, "Journalists", "Media professionals researching energy stories")  
    Person(student, "Students", "Academic users learning about energy systems")
    Person(policymaker, "Policymakers", "Government officials making energy decisions")

    System(decipher, "Swiss Energy Scenarios Decipher System", "Multiagent AI system for energy scenario analysis")

    System_Ext(openai, "OpenAI API", "GPT-4 language model services")
    System_Ext(bfe, "Swiss Federal Office of Energy", "Energy Perspectives 2050+ data source")

    Rel(citizen, decipher, "Asks questions about energy scenarios", "HTTPS")
    Rel(journalist, decipher, "Researches energy stories and data", "HTTPS")
    Rel(student, decipher, "Studies energy transition concepts", "HTTPS")
    Rel(policymaker, decipher, "Analyzes policy implications", "HTTPS")

    Rel(decipher, openai, "Sends queries for AI processing", "HTTPS/API")
    Rel(decipher, bfe, "Processes energy scenario data", "Local Files")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

### Key External Entities:
- **Citizens, Journalists, Students, Policymakers**: Primary user groups with different information needs
- **OpenAI API**: Provides GPT-4 language model capabilities for intelligent query processing
- **Swiss Federal Office of Energy**: Source of Energy Perspectives 2050+ datasets and reports

---

## Level 2: Container Diagram

```mermaid
C4Container
    title Container Diagram - Swiss Energy Scenarios Decipher System

    Person(users, "System Users", "Citizens, Journalists, Students, Policymakers")

    Container_Boundary(system, "Swiss Energy Scenarios Decipher System") {
        Container(web_ui, "Web Interface", "Streamlit", "Modern web-based user interface with interactive features")
        Container(cli_ui, "CLI Interface", "Python CLI", "Command-line interactive chat interface")
        
        Container(orchestrator, "Orchestrator Service", "Python/AsyncIO", "Central coordinator that routes queries and synthesizes responses")
        
        Container(data_agent, "Data Interpreter Agent", "Python/Pandas", "Analyzes CSV energy data and provides statistics")
        Container(scenario_agent, "Scenario Analyst Agent", "Python/Analytics", "Compares energy transition scenarios")
        Container(doc_agent, "Document Intelligence Agent", "Python/PyPDF2", "Processes PDF reports and technical documents")
        Container(policy_agent, "Policy Context Agent", "Python/Knowledge", "Provides Swiss energy policy expertise")
        
        Container(csv_processor, "CSV Data Processor", "Python/Pandas", "Handles 87 CSV files with energy statistics")
        Container(pdf_processor, "PDF Document Processor", "Python/PyPDF2", "Processes 16 technical PDF reports")
        Container(config, "Configuration Service", "Python/dotenv", "Manages API keys and system settings")
    }

    ContainerDb(data_files, "Energy Data Files", "CSV/PDF", "103 data files: synthesis data, transformation data, technical reports")

    System_Ext(openai, "OpenAI API", "GPT-4 language model")

    Rel(users, web_ui, "Interacts with", "HTTPS")
    Rel(users, cli_ui, "Uses", "Terminal")

    Rel(web_ui, orchestrator, "Sends queries", "Python calls")
    Rel(cli_ui, orchestrator, "Sends queries", "Python calls")

    Rel(orchestrator, data_agent, "Routes data queries", "Python calls")
    Rel(orchestrator, scenario_agent, "Routes scenario queries", "Python calls") 
    Rel(orchestrator, doc_agent, "Routes document queries", "Python calls")
    Rel(orchestrator, policy_agent, "Routes policy queries", "Python calls")

    Rel(data_agent, csv_processor, "Requests data analysis", "Python calls")
    Rel(scenario_agent, csv_processor, "Requests scenario data", "Python calls")
    Rel(doc_agent, pdf_processor, "Requests document analysis", "Python calls")

    Rel(csv_processor, data_files, "Reads CSV files", "File I/O")
    Rel(pdf_processor, data_files, "Reads PDF files", "File I/O")

    Rel_Back(data_agent, openai, "AI processing requests", "HTTPS/API")
    Rel_Back(scenario_agent, openai, "AI processing requests", "HTTPS/API") 
    Rel_Back(doc_agent, openai, "AI processing requests", "HTTPS/API")
    Rel_Back(policy_agent, openai, "AI processing requests", "HTTPS/API")
    Rel_Back(orchestrator, openai, "AI processing requests", "HTTPS/API")

    Rel(config, orchestrator, "Provides configuration", "Python import")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

### Key Containers:
- **User Interfaces**: Web (Streamlit) and CLI for different interaction preferences
- **AI Agents**: 5 specialized agents for different aspects of energy analysis
- **Data Processors**: Dedicated components for CSV and PDF file processing
- **Configuration**: Centralized management of API keys and system settings

---

## Level 3: Component Diagram - Orchestrator Service

```mermaid
C4Component
    title Component Diagram - Orchestrator Service

    Container(web_ui, "Web Interface", "Streamlit", "User interaction layer")
    Container(cli_ui, "CLI Interface", "Python CLI", "Command-line interface")

    Container_Boundary(orchestrator, "Orchestrator Service") {
        Component(query_router, "Query Router", "Python Class", "Analyzes queries and determines appropriate agents")
        Component(response_synthesizer, "Response Synthesizer", "Python Class", "Combines responses from multiple agents")
        Component(agent_registry, "Agent Registry", "Python Dict", "Maintains registry of available specialist agents")
        Component(conversation_manager, "Conversation Manager", "Python Class", "Manages conversation history and context")
        Component(user_adapter, "User Type Adapter", "Python Class", "Adapts responses for different user types")
    }

    Container(data_agent, "Data Interpreter Agent", "Python/Pandas", "Data analysis specialist")
    Container(scenario_agent, "Scenario Analyst Agent", "Python/Analytics", "Scenario comparison specialist")
    Container(doc_agent, "Document Intelligence Agent", "Python/PyPDF2", "Document processing specialist")
    Container(policy_agent, "Policy Context Agent", "Python/Knowledge", "Policy expertise specialist")

    System_Ext(openai, "OpenAI API", "GPT-4 language model")

    Rel(web_ui, query_router, "Sends user query", "Python call")
    Rel(cli_ui, query_router, "Sends user query", "Python call")

    Rel(query_router, agent_registry, "Gets available agents", "Python call")
    Rel(query_router, openai, "Analyzes query routing", "HTTPS/API")

    Rel(query_router, data_agent, "Routes data queries", "Async Python call")
    Rel(query_router, scenario_agent, "Routes scenario queries", "Async Python call")
    Rel(query_router, doc_agent, "Routes document queries", "Async Python call")
    Rel(query_router, policy_agent, "Routes policy queries", "Async Python call")

    Rel(data_agent, response_synthesizer, "Returns response", "Python return")
    Rel(scenario_agent, response_synthesizer, "Returns response", "Python return")
    Rel(doc_agent, response_synthesizer, "Returns response", "Python return")
    Rel(policy_agent, response_synthesizer, "Returns response", "Python return")

    Rel(response_synthesizer, user_adapter, "Adapts response", "Python call")
    Rel(response_synthesizer, openai, "Synthesizes responses", "HTTPS/API")
    Rel(user_adapter, conversation_manager, "Stores conversation", "Python call")

    Rel(conversation_manager, web_ui, "Returns final response", "Python return")
    Rel(conversation_manager, cli_ui, "Returns final response", "Python return")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

### Key Components:
- **Query Router**: Intelligent routing based on query analysis
- **Response Synthesizer**: Combines multiple agent responses coherently  
- **Agent Registry**: Dynamic management of specialist agents
- **User Type Adapter**: Customizes responses for different user personas

---

## Level 4: Code Structure - Data Interpreter Agent

```mermaid
C4Component
    title Code Structure - Data Interpreter Agent

    Container_Boundary(data_agent, "Data Interpreter Agent") {
        Component(agent_controller, "DataInterpreterAgent", "Main Class", "Primary agent interface and coordination")
        Component(data_catalog, "Data Catalog Builder", "Method", "Builds catalog of available CSV files and metadata")
        Component(relevance_finder, "Relevance Identifier", "Method", "Identifies relevant data files for queries")
        Component(data_analyzer, "Data Analyzer", "Method", "Performs statistical analysis on datasets")
        Component(response_generator, "Response Generator", "Method", "Generates natural language responses from analysis")
        Component(confidence_calculator, "Confidence Calculator", "Method", "Calculates confidence scores for responses")
    }

    Container(csv_processor, "CSV Data Processor", "Python Class", "Handles CSV file operations")
    Container(base_agent, "Base Agent", "Abstract Class", "Common agent functionality")
    System_Ext(openai, "OpenAI API", "GPT-4 processing")

    Rel(agent_controller, base_agent, "Inherits from", "Python inheritance")
    Rel(agent_controller, data_catalog, "Builds data catalog", "Method call")
    Rel(agent_controller, csv_processor, "Processes CSV files", "Composition")

    Rel(agent_controller, relevance_finder, "Identifies relevant data", "Method call")
    Rel(relevance_finder, data_catalog, "Queries catalog", "Method call")

    Rel(agent_controller, data_analyzer, "Analyzes data", "Method call")
    Rel(data_analyzer, csv_processor, "Loads and processes data", "Method call")

    Rel(agent_controller, response_generator, "Generates response", "Method call")
    Rel(response_generator, openai, "AI processing", "HTTPS/API")

    Rel(agent_controller, confidence_calculator, "Calculates confidence", "Method call")
    Rel(confidence_calculator, data_analyzer, "Uses analysis results", "Method call")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

---

## Data Flow Architecture

### Query Processing Flow:

```mermaid
flowchart TD
    A[User Query] --> B[Orchestrator Agent]
    B --> C{Query Analysis}
    C --> D[Route to Specialist Agents]
    
    D --> E[Data Interpreter Agent]
    D --> F[Scenario Analyst Agent]  
    D --> G[Document Intelligence Agent]
    D --> H[Policy Context Agent]
    
    E --> I[CSV Data Processing]
    F --> J[Scenario Comparison]
    G --> K[PDF Document Analysis]
    H --> L[Policy Knowledge Base]
    
    I --> M[Statistical Analysis]
    J --> N[Pathway Comparison]
    K --> O[Document Extraction]
    L --> P[Policy Context]
    
    M --> Q[Response Synthesis]
    N --> Q
    O --> Q  
    P --> Q
    
    Q --> R[User Type Adaptation]
    R --> S[Final Response]
    S --> T[User Interface]
```

### Data Processing Architecture:

```mermaid
flowchart LR
    subgraph "Data Sources"
        A[87 CSV Files<br/>Synthesis Data]
        B[13 CSV Files<br/>Transformation Data] 
        C[16 PDF Reports<br/>Technical Documents]
    end
    
    subgraph "Data Processors"
        D[CSV Processor<br/>Pandas-based]
        E[PDF Processor<br/>PyPDF2-based]
    end
    
    subgraph "AI Agents"
        F[Data Interpreter<br/>Statistics & Trends]
        G[Scenario Analyst<br/>Pathway Comparison]
        H[Document Intelligence<br/>Report Analysis]
    end
    
    subgraph "AI Processing"
        I[OpenAI GPT-4<br/>Natural Language]
    end
    
    A --> D
    B --> D
    C --> E
    
    D --> F
    D --> G
    E --> H
    
    F --> I
    G --> I
    H --> I
```

---

## Deployment Architecture

### Development/Local Deployment:

```mermaid
C4Deployment
    title Deployment Diagram - Local Development

    Deployment_Node(dev_machine, "Developer Machine", "macOS/Linux/Windows") {
        Deployment_Node(python_env, "Python Virtual Environment", "Python 3.8+") {
            Container(web_app, "Streamlit Web App", "streamlit run", "Web interface on port 8501")
            Container(cli_app, "CLI Application", "python main.py", "Command-line interface")
            Container(agents, "AI Agent System", "Python processes", "5 specialist agents + orchestrator")
        }
        
        Deployment_Node(local_storage, "Local File System", "Data directory") {
            ContainerDb(csv_files, "CSV Data", "87 files", "Energy statistics and projections")
            ContainerDb(pdf_files, "PDF Reports", "16 files", "Technical documentation")
        }
    }

    Deployment_Node(openai_cloud, "OpenAI Cloud", "External API") {
        Container(gpt4, "GPT-4 Service", "AI Language Model", "Natural language processing")
    }

    Rel(web_app, agents, "Python calls", "In-process")
    Rel(cli_app, agents, "Python calls", "In-process")
    Rel(agents, csv_files, "File I/O", "Local reads")
    Rel(agents, pdf_files, "File I/O", "Local reads")
    Rel(agents, gpt4, "HTTPS API calls", "Internet")

    UpdateLayoutConfig($c4ShapeInRow="2", $c4BoundaryInRow="1")
```

### Production Deployment Options:

```mermaid
C4Deployment
    title Deployment Diagram - Production Options

    Deployment_Node(cloud, "Cloud Platform", "AWS/Azure/GCP") {
        Deployment_Node(web_tier, "Web Tier", "Load Balanced") {
            Container(streamlit_app, "Streamlit Apps", "Multiple instances", "Horizontal scaling")
        }
        
        Deployment_Node(app_tier, "Application Tier", "Container Platform") {
            Container(agent_services, "Agent Services", "Docker containers", "Microservices architecture")
        }
        
        Deployment_Node(data_tier, "Data Tier", "Persistent Storage") {
            ContainerDb(object_storage, "Object Storage", "S3/Blob", "CSV and PDF files")
            ContainerDb(cache_db, "Cache Database", "Redis", "Response caching")
        }
    }

    System_Ext(openai_api, "OpenAI API", "External service")
    Person(users, "End Users", "Web browsers")

    Rel(users, streamlit_app, "HTTPS", "Web requests")
    Rel(streamlit_app, agent_services, "HTTP API", "Internal API")
    Rel(agent_services, object_storage, "Data access", "File reads")
    Rel(agent_services, cache_db, "Caching", "Performance")
    Rel(agent_services, openai_api, "AI processing", "HTTPS")

    UpdateLayoutConfig($c4ShapeInRow="1", $c4BoundaryInRow="3")
```

---

## Technical Decisions & Rationale

### Architecture Decisions:

| Decision | Rationale |
|----------|-----------|
| **Multiagent Architecture** | Enables specialization, parallel processing, and modular development |
| **Python Ecosystem** | Rich data science libraries (Pandas, NumPy), AI integration (OpenAI), rapid development |
| **Asynchronous Processing** | Enables parallel agent execution for better performance |
| **Streamlit for Web UI** | Rapid prototyping, built-in interactivity, minimal web development overhead |
| **File-based Data Storage** | Simplicity, direct access to Swiss government data formats, no database complexity |
| **OpenAI GPT-4** | State-of-the-art natural language understanding and generation |

### Agent Specialization Strategy:

| Agent | Specialization | Data Sources | Key Capabilities |
|-------|---------------|--------------|-----------------|
| **Data Interpreter** | Statistics & Analytics | 87 CSV files | Time series analysis, scenario comparison, quantitative insights |
| **Scenario Analyst** | Pathway Comparison | CSV + Knowledge | ZERO vs WWB analysis, assumption comparison, feasibility assessment |
| **Document Intelligence** | Report Processing | 16 PDF files | Methodology extraction, technical analysis, multilingual processing |
| **Policy Context** | Regulatory Knowledge | Swiss policy framework | Implementation pathways, stakeholder analysis, regulatory compliance |
| **Orchestrator** | Coordination | All agents | Query routing, response synthesis, conversation management |

---

## Quality Attributes

### Performance:
- **Parallel Processing**: Agents execute queries simultaneously using AsyncIO
- **Caching**: Data catalog and file processing results are cached
- **Streaming**: Streamlit provides responsive web interface updates

### Reliability:
- **Error Handling**: Comprehensive exception handling across all components
- **Graceful Degradation**: System continues operating if individual agents fail
- **Confidence Scoring**: Users understand reliability of responses

### Scalability:
- **Horizontal Scaling**: Web interface can be deployed in multiple instances
- **Agent Isolation**: Each agent is independently scalable
- **Stateless Design**: No persistent state between requests

### Security:
- **API Key Management**: Secure storage using environment variables
- **Input Validation**: Query sanitization and validation
- **Rate Limiting**: OpenAI API usage monitoring and control

### Maintainability:
- **Modular Design**: Clear separation of concerns between components
- **Abstract Base Classes**: Common patterns for agent development
- **Configuration Management**: Centralized system configuration
- **Comprehensive Testing**: Unit tests and integration tests provided

---

## Future Architecture Considerations

### Potential Enhancements:

1. **Vector Database Integration**: For semantic search across documents
2. **Real-time Data Pipeline**: For live energy data updates
3. **Multi-model AI**: Integration with multiple AI providers
4. **API Gateway**: For external system integration
5. **Monitoring & Observability**: Application performance monitoring
6. **User Authentication**: For personalized experiences
7. **Collaboration Features**: Shared workspaces and annotations

### Scaling Considerations:

1. **Microservices**: Split agents into independent services
2. **Message Queue**: Asynchronous agent communication
3. **Database Layer**: Structured data storage for better query performance
4. **CDN Integration**: Faster static asset delivery
5. **Auto-scaling**: Dynamic resource allocation based on demand

This C4 architecture provides a comprehensive view of the Swiss Energy Scenarios Decipher System, from high-level context to detailed component interactions, supporting both current functionality and future growth.