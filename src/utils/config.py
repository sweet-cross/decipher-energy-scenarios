import os
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Dict, Any

load_dotenv()

@dataclass
class Config:
    openai_api_key: str
    data_path: str
    reports_path: str
    model_name: str = "gpt-4"
    temperature: float = 0.3
    max_tokens: int = 2000
    
    @classmethod
    def from_env(cls) -> 'Config':
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            data_path=os.path.join(os.path.dirname(__file__), "../../data"),
            reports_path=os.path.join(os.path.dirname(__file__), "../../data/reports"),
            model_name=os.getenv("MODEL_NAME", "gpt-4"),
            temperature=float(os.getenv("TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("MAX_TOKENS", "2000"))
        )
        
    def validate(self) -> bool:
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        return True

config = Config.from_env()