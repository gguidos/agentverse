"""
Mock implementations for testing
"""

from typing import Any, Dict, List
from src.core.agentverse.llm import BaseLLM

class MockLLM(BaseLLM):
    """Mock LLM implementation"""
    
    async def generate(self, prompt: str) -> str:
        """Generate mock response"""
        return "Mock response"
    
    async def generate_response(self, prompt: str) -> str:
        """Generate mock response"""
        return await self.generate(prompt)
    
    async def get_embeddings(self, text: str) -> List[float]:
        """Get mock embeddings"""
        return [0.1, 0.2, 0.3]  # Mock embedding vector
    
    async def evaluate(self, text: str) -> Dict[str, Any]:
        """Evaluate mock text"""
        return {
            "score": 0.8,
            "reasoning": "Mock evaluation"
        } 