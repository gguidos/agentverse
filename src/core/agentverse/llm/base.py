"""Base LLM Module"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    """LLM Configuration"""
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    max_retries: int = 3

class LLMResult(BaseModel):
    """LLM Response Result"""
    content: str
    raw_response: Dict[str, Any] = Field(default_factory=dict)

class BaseLLM:
    """Base LLM class"""
    
    def __init__(self, config: Optional[LLMConfig] = None, **kwargs):
        """Initialize LLM"""
        self.config = config or LLMConfig(**kwargs)
    
    async def generate_response(self, prompt: str) -> LLMResult:
        """Generate response from prompt"""
        raise NotImplementedError 