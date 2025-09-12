
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from dataclasses import dataclass
import json
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

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
    agents_involved: List[str] = None

class BaseAgent(ABC):
    def __init__(self, name: str, description: str, openai_api_key: str,
                 model: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None):
        self.name = name
        self.description = description
        self.model = model or os.getenv("MODEL_NAME", "gpt-4")
        import logging
        logger = logging.getLogger(__name__)
        temp_val = None
        if temperature is not None:
            try:
                temp_val = float(temperature)
            except (TypeError, ValueError):
                logger.warning(f"Invalid temperature value '{temperature}', falling back to 0.3.")
                temp_val = 0.3
        else:
            try:
                temp_val = float(os.getenv("TEMPERATURE", "0.3"))
            except (TypeError, ValueError):
                logger.warning(f"Invalid TEMPERATURE env var, falling back to 0.3.")
                temp_val = 0.3
        # Clamp to [0.0, 2.0]
        if temp_val < 0.0:
            logger.warning(f"Clamping temperature {temp_val} to 0.0.")
            temp_val = 0.0
        elif temp_val > 2.0:
            logger.warning(f"Clamping temperature {temp_val} to 2.0.")
            temp_val = 2.0
        self.temperature = temp_val

        if max_tokens is not None:
            try:
                mt_val = int(max_tokens)
                if mt_val > 0:
                    self.max_tokens = mt_val
                else:
                    logger.warning(f"Invalid max_tokens value '{max_tokens}', falling back to 2000.")
                    self.max_tokens = 2000
            except (TypeError, ValueError):
                logger.warning(f"Non-integer max_tokens value '{max_tokens}', falling back to 2000.")
                self.max_tokens = 2000
        else:
            try:
                mt_env = int(os.getenv("MAX_TOKENS", "2000"))
                if mt_env > 0:
                    self.max_tokens = mt_env
                else:
                    logger.warning(f"Invalid MAX_TOKENS env var '{mt_env}', falling back to 2000.")
                    self.max_tokens = 2000
            except (TypeError, ValueError):
                logger.warning(f"Non-integer MAX_TOKENS env var, falling back to 2000.")
                self.max_tokens = 2000
        self.client = AsyncOpenAI(api_key=openai_api_key)
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
    
    async def _call_openai(self, messages: List[Dict[str, str]], max_retries: int = 3, timeout: float = 30.0) -> str:
        """Make async API call to OpenAI with retries and timeout."""
        last_err = None
        for attempt in range(max_retries):
            try:
                coro = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                response = await asyncio.wait_for(coro, timeout=timeout)
                return response.choices[0].message.content
            except Exception as err:
                last_err = err
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        raise Exception(f"OpenAI API error in {self.name}: {str(last_err)}") from last_err
    
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
