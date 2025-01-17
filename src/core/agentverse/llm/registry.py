"""LLM Registry Module"""

from typing import Dict, Type
from src.core.agentverse.llm.base import BaseLLM

class LLMRegistry:
    """LLM Registry"""
    
    def __init__(self):
        self._llms: Dict[str, Type[BaseLLM]] = {}
    
    def register(self, llm_type: str, llm_class: Type[BaseLLM]) -> None:
        """Register LLM implementation"""
        self._llms[llm_type] = llm_class
    
    def get(self, llm_type: str) -> Type[BaseLLM]:
        """Get LLM implementation"""
        if llm_type not in self._llms:
            raise ValueError(f"Unknown LLM type: {llm_type}")
        return self._llms[llm_type]
    
    def list(self) -> Dict[str, Type[BaseLLM]]:
        """List registered LLMs"""
        return self._llms.copy()

# Global registry instance
registry = LLMRegistry() 