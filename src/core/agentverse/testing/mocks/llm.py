"""Mock LLM implementation"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from src.core.agentverse.llm.base import BaseLLM, LLMResult, LLMConfig

class MockLLMConfig(LLMConfig):
    """Mock LLM Configuration"""
    mock_responses: List[str] = ["Mock response"]

class MockLLM(BaseLLM):
    """Mock LLM for testing"""
    
    def __init__(
        self,
        responses: Optional[List[str]] = None,
        config: Optional[MockLLMConfig] = None,
        **kwargs
    ):
        """Initialize mock LLM"""
        super().__init__(config=config or MockLLMConfig(**kwargs))
        self.mock_responses = responses or self.config.mock_responses
        self.current_index = 0
        self.call_history = []
    
    async def generate_response(self, prompt: str) -> LLMResult:
        """Generate mock response"""
        # Record call
        self.call_history.append({
            "prompt": prompt,
            "timestamp": datetime.utcnow()
        })
        
        # Get next response
        response = self.mock_responses[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.mock_responses)
        
        return LLMResult(
            content=response,
            raw_response={"prompt": prompt}
        ) 