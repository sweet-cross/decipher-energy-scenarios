from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import openai
from dataclasses import dataclass
import json
import asyncio

@dataclass
class AgentMessage:
    role: str  # 'system', 'user', 'assistant'
    content: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass 
class AgentResponse:
    content: str
    confidence: float
    data_sources: List[str] = None
    reasoning: Optional[str] = None
    suggestions: List[str] = None

class BaseAgent(ABC):
    def __init__(self, name: str, description: str, openai_api_key: str, 
                 model: str = "gpt-4", temperature: float = 0.3, max_tokens: int = 2000):
        self.name = name
        self.description = description
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.system_prompt = self._build_system_prompt()
        
    @abstractmethod
    def _build_system_prompt(self) -> str:
        """Build the system prompt specific to this agent."""
        pass
    
    @abstractmethod
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Process a query and return a response."""
        pass
    
    def _prepare_messages(self, query: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Prepare messages for OpenAI API call."""
        messages = [{"role": "system", "content": self.system_prompt}]
        
        if context:
            context_str = f"Context: {json.dumps(context, indent=2)}"
            messages.append({"role": "system", "content": context_str})
            
        messages.append({"role": "user", "content": query})
        return messages
    
    async def _call_openai(self, messages: List[Dict[str, str]]) -> str:
        """Make API call to OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error in {self.name}: {str(e)}")
    
    def _extract_confidence(self, response_text: str) -> float:
        """Extract confidence level from response text."""
        # Simple confidence extraction - look for confidence indicators
        confidence_keywords = {
            "certainly": 0.9, "definitely": 0.9, "clearly": 0.85,
            "likely": 0.7, "probably": 0.7, "appears": 0.6,
            "possibly": 0.5, "might": 0.4, "unclear": 0.3,
            "uncertain": 0.2, "unknown": 0.1
        }
        
        response_lower = response_text.lower()
        max_confidence = 0.6  # default
        
        for keyword, confidence in confidence_keywords.items():
            if keyword in response_lower:
                max_confidence = max(max_confidence, confidence)
                
        return max_confidence
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return agent capabilities."""
        return {
            "name": self.name,
            "description": self.description,
            "specialization": self.__class__.__name__,
            "model": self.model
        }