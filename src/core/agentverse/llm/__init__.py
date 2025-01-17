"""LLM Package"""

from typing import Dict, Type, Any
from src.core.agentverse.llm.base import BaseLLM
from src.core.agentverse.llm.registry import registry

def register_llm(llm_type: str, llm_class: Type[BaseLLM]) -> None:
    """Register LLM implementation"""
    registry.register(llm_type, llm_class)

def get_llm(llm_type: str, **config) -> BaseLLM:
    """Get LLM implementation"""
    llm_class = registry.get(llm_type)
    return llm_class(**config)

__all__ = [
    "BaseLLM",
    "register_llm",
    "get_llm"
] 