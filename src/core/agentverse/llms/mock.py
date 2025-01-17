"""Mock LLM implementation for testing"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from src.core.agentverse.llms.base import BaseLLM

class MockLLMConfig(BaseModel):
    """Configuration for mock LLM"""
    type: str = "mock"
    responses: List[str] = Field(default_factory=list)
    current_index: int = 0

class MockLLM(BaseLLM):
    """Mock LLM implementation that returns predefined responses"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = MockLLMConfig(**config)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Return next predefined response"""
        if not self.config.responses:
            return "Mock response"
            
        response = self.config.responses[self.config.current_index]
        self.config.current_index = (self.config.current_index + 1) % len(self.config.responses)
        return response
    
    async def stream(self, prompt: str, **kwargs) -> str:
        """Stream is same as generate for mock"""
        return await self.generate(prompt, **kwargs) 