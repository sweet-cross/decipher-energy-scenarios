# 🔌 Swiss Energy Scenarios Decipher System - API Documentation

## Agent API Interface

### Base Agent Interface

All agents inherit from the `BaseAgent` class and implement the following interface:

```python
class BaseAgent(ABC):
    def __init__(self, name: str, description: str, openai_api_key: str, 
                 model: str = "gpt-4", temperature: float = 0.3, max_tokens: int = 2000)
    
    @abstractmethod
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse
    
    def get_capabilities(self) -> Dict[str, Any]
```

### Agent Response Format

```python
@dataclass 
class AgentResponse:
    content: str                    # Main response content
    confidence: float              # Confidence score (0.0 - 1.0)
    data_sources: List[str]        # List of data sources used
    reasoning: Optional[str]       # Analysis reasoning
    suggestions: List[str]         # Follow-up suggestions
```

---

## Orchestrator Agent API

### Primary Interface

```python
class OrchestratorAgent(BaseAgent):
    def __init__(self, openai_api_key: str, agents_registry: Dict[str, BaseAgent] = None)
    def register_agent(self, agent: BaseAgent)
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse
```

### Usage Example

```python
# Initialize orchestrator
orchestrator = OrchestratorAgent(api_key)

# Register specialist agents
orchestrator.register_agent(DataInterpreterAgent(api_key, data_path))
orchestrator.register_agent(ScenarioAnalystAgent(api_key, data_path))

# Process query
context = {"user_type": "citizen"}
response = await orchestrator.process_query("What are CO2 emissions in 2030?", context)

print(f"Response: {response.content}")
print(f"Confidence: {response.confidence}")
print(f"Sources: {response.data_sources}")
```

---

## Data Interpreter Agent API

### Specialized Interface

```python
class DataInterpreterAgent(BaseAgent):
    def __init__(self, openai_api_key: str, data_path: str)
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse
    
    # Internal methods
    def _identify_relevant_data(self, query: str) -> List[Dict[str, str]]
    async def _analyze_data(self, query: str, relevant_files: List[Dict[str, str]], 
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]
```

### Supported Query Types

| Query Pattern | Example | Data Sources |
|---------------|---------|--------------|
| **Emissions queries** | "CO2 emissions in 2030" | `emissions_*.csv` files |
| **Energy consumption** | "Electricity consumption by sector" | `*_consumption_*.csv` files |
| **Renewable energy** | "Solar capacity growth" | `renewable_*.csv` files |
| **Transport analysis** | "Electric vehicle adoption" | `transport_*.csv` files |
| **Building sector** | "Heat pump deployment" | `buildings_*.csv` files |

### Response Example

```python
response = await data_agent.process_query("What are Switzerland's CO2 emissions in 2030?")

# Expected response structure:
{
    "content": "Switzerland's CO2 emissions in 2030 under the ZERO-Basis scenario are projected to be 25.3 million tonnes, representing a 45% reduction from 1990 levels...",
    "confidence": 0.87,
    "data_sources": ["synthesis/02-02-emissions_co2.csv"],
    "reasoning": "Analyzed CO2 emissions data across scenarios with focus on 2030 projections",
    "suggestions": ["Compare emissions across different scenarios", "Analyze sectoral breakdown of CO2 emissions"]
}
```

---

## Scenario Analyst Agent API

### Specialized Interface

```python
class ScenarioAnalystAgent(BaseAgent):
    def __init__(self, openai_api_key: str, data_path: str)
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse
    
    # Internal methods
    def _identify_scenarios(self, query: str) -> List[str]
    async def _gather_comparison_data(self, query: str, scenarios: List[str]) -> Dict[str, Any]
    def compare_scenarios(self, filename: str, variable: str, scenarios: List[str]) -> pd.DataFrame
```

### Scenario Types

| Scenario | Description | Key Features |
|----------|-------------|--------------|
| **ZERO-Basis** | Net-zero by 2050 pathway | Accelerated renewables, electrification, efficiency |
| **WWB** | Business as usual | Current policy continuation, moderate changes |
| **Variants** | Alternative assumptions | Different nuclear/renewable mixes, carbon pricing |

### Usage Example

```python
response = await scenario_agent.process_query("Compare ZERO vs WWB scenarios for transport")

# Response includes:
# - Key differences between scenarios
# - Quantified impacts and timelines  
# - Implementation challenges
# - Policy implications
```

---

## Document Intelligence Agent API

### Specialized Interface

```python
class DocumentIntelligenceAgent(BaseAgent):
    def __init__(self, openai_api_key: str, reports_path: str)
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse
    
    # Internal methods
    def _identify_relevant_documents(self, query: str) -> List[Dict[str, Any]]
    async def _extract_information(self, query: str, relevant_docs: List[Dict[str, Any]]) -> Dict[str, Any]
```

### Document Categories

| Document Type | Pattern | Content Focus |
|---------------|---------|---------------|
| **Technical Reports** | `*technischer*.pdf` | Detailed methodologies, modeling approaches |
| **Executive Summaries** | `*kurzbericht*.pdf` | Key findings, policy implications |
| **Fact Sheets** | `*faktenblatt*.pdf` | Concise data presentations |
| **Specialized Studies** | `*exkurs*.pdf` | Deep-dives on specific topics |

### Usage Example

```python
response = await doc_agent.process_query("What methodology is used for scenario modeling?")

# Response includes:
# - Methodology explanations from technical reports
# - Model validation approaches  
# - Uncertainty assessments
# - Document citations and page references
```

---

## Policy Context Agent API

### Specialized Interface

```python
class PolicyContextAgent(BaseAgent):
    def __init__(self, openai_api_key: str)
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse
    
    # Internal methods
    def _identify_policy_areas(self, query: str) -> List[str]
    async def _analyze_policy_implications(self, query: str, policy_areas: List[str], 
                                          context: Optional[Dict[str, Any]] = None) -> AgentResponse
```

### Policy Knowledge Areas

| Policy Area | Coverage |
|-------------|----------|
| **Energy Strategy 2050** | Constitutional framework, renewable targets, efficiency goals |
| **CO2 Act** | Climate policy, emissions targets, carbon pricing |
| **Federal Energy Act** | Regulatory framework, grid planning, market design |
| **Cantonal Policies** | Spatial planning, building codes, implementation |

---

## Data Processing APIs

### CSV Processor

```python
class CSVProcessor:
    def __init__(self, data_path: str)
    
    def get_available_files(self) -> Dict[str, List[str]]
    def load_csv(self, filename: str, category: str = "synthesis") -> pd.DataFrame
    def search_data_by_keywords(self, keywords: List[str], category: Optional[str] = None) -> Dict[str, pd.DataFrame]
    def filter_data(self, filename: str, category: str = "synthesis", 
                   scenario: Optional[str] = None, variant: Optional[str] = None,
                   year_range: Optional[Tuple[int, int]] = None) -> pd.DataFrame
    def get_data_summary(self, filename: str, category: str = "synthesis") -> Dict[str, any]
    def compare_scenarios(self, filename: str, variable: str, scenarios: List[str]) -> pd.DataFrame
```

### PDF Processor

```python
class PDFProcessor:
    def __init__(self, reports_path: str)
    
    def get_available_reports(self) -> List[str]
    def extract_text(self, pdf_filename: str) -> str
    def search_text(self, query: str, pdf_filename: Optional[str] = None) -> Dict[str, List[str]]
    def get_document_summary(self, pdf_filename: str) -> Dict[str, any]
    def extract_key_sections(self, pdf_filename: str, sections: List[str]) -> Dict[str, str]
```

---

## Configuration API

### Environment Configuration

```python
@dataclass
class Config:
    openai_api_key: str
    data_path: str
    reports_path: str
    model_name: str = "gpt-4"
    temperature: float = 0.3
    max_tokens: int = 2000
    
    @classmethod
    def from_env(cls) -> 'Config'
    def validate(self) -> bool
```

### Usage

```python
from utils.config import config

# Validate configuration
config.validate()

# Access settings
api_key = config.openai_api_key
model = config.model_name
```

---

## Error Handling

### Standard Error Responses

```python
# Agent processing errors
try:
    response = await agent.process_query(query)
except Exception as e:
    response = AgentResponse(
        content=f"Error processing query: {str(e)}",
        confidence=0.0,
        data_sources=[],
        reasoning="Agent encountered an error during processing"
    )
```

### Common Error Types

| Error Type | Cause | Handling |
|------------|-------|----------|
| **FileNotFoundError** | Missing data files | Graceful degradation with error message |
| **OpenAI API Error** | API rate limits, invalid key | Retry logic with exponential backoff |
| **Data Processing Error** | Malformed CSV/PDF files | Skip problematic files, continue processing |
| **Query Parsing Error** | Ambiguous or unsupported queries | Request clarification from user |

---

## Performance Considerations

### Caching Strategy

```python
# Agent-level caching
class DataInterpreterAgent:
    def __init__(self):
        self._cache = {}  # File content cache
        self.data_catalog = self._build_data_catalog()  # Metadata cache
```

### Async Processing

```python
# Parallel agent execution
async def _route_to_agents(self, query: str, routing_decision: Dict[str, Any]) -> Dict[str, AgentResponse]:
    tasks = []
    for agent_name in routing_decision.get("primary_agents", []):
        if agent_name in self.agents_registry:
            agent = self.agents_registry[agent_name]
            task = agent.process_query(query, context)
            tasks.append((agent_name, task))
    
    # Execute in parallel
    results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
    return self._process_results(results)
```

### Memory Management

- **Lazy Loading**: Data files loaded only when needed
- **LRU Cache**: Most recently used data kept in memory
- **Streaming**: Large datasets processed in chunks

---

## Integration Examples

### CLI Integration

```python
from interfaces.cli_interface import EnergyScenariosCLI

cli = EnergyScenariosCLI()
await cli.run()
```

### Web Integration

```python
import streamlit as st
from streamlit_app import process_query

# In Streamlit app
if st.button("Analyze"):
    response = await process_query(user_query, user_type)
    st.write(response.content)
    st.metric("Confidence", response.confidence)
```

### Custom Integration

```python
# Initialize system
orchestrator = OrchestratorAgent(api_key)
# ... register agents

# Custom processing pipeline
async def analyze_energy_question(question: str, user_context: dict) -> dict:
    response = await orchestrator.process_query(question, user_context)
    
    return {
        "answer": response.content,
        "confidence": response.confidence,
        "sources": response.data_sources,
        "follow_ups": response.suggestions
    }
```

This API documentation provides comprehensive guidance for integrating with and extending the Swiss Energy Scenarios Decipher System.