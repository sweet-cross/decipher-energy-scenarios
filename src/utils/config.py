def _parse_env_int(varname: str, default: int, min_value: int = 1) -> int:
    val = os.getenv(varname, None)
    try:
        if val is None or val.strip() == "":
            return max(min_value, default)
        parsed = int(val)
        return max(min_value, parsed)
    except (TypeError, ValueError):
        return max(min_value, default)

def _parse_env_float(varname: str, default: float, min_value: float = 0.0) -> float:
    val = os.getenv(varname, None)
    try:
        if val is None or val.strip() == "":
            return max(min_value, default)
        parsed = float(val)
        return max(min_value, parsed)
    except (TypeError, ValueError):
        return max(min_value, default)
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
    # Index/ingestion thresholds
    min_figure_width: int = 220
    min_figure_height: int = 160
    min_figure_area: int = 60000

    def __post_init__(self):
        """Validate figure dimension constraints."""
        min_possible_area = self.min_figure_width * self.min_figure_height
        if self.min_figure_area < min_possible_area:
            raise ValueError(
                f"min_figure_area ({self.min_figure_area}) cannot be less than "
                f"min_figure_width × min_figure_height ({min_possible_area})"
            )
    
    @classmethod
    def from_env(cls) -> 'Config':
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            data_path=os.path.join(os.path.dirname(__file__), "../../data"),
            reports_path=os.path.join(os.path.dirname(__file__), "../../data/reports"),
            model_name=os.getenv("MODEL_NAME", "gpt-4"),
            temperature=_parse_env_float("TEMPERATURE", 0.3, 0.0),
            max_tokens=_parse_env_int("MAX_TOKENS", 2000, 1),
            min_figure_width=_parse_env_int("MIN_FIGURE_WIDTH", 220, 1),
            min_figure_height=_parse_env_int("MIN_FIGURE_HEIGHT", 160, 1),
            min_figure_area=_parse_env_int("MIN_FIGURE_AREA", 60000, 1),
        )
        
    def validate(self) -> bool:
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        return True

config = Config.from_env()
