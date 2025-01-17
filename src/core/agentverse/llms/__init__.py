"""LLM implementations"""

from typing import Dict, Any, Type
from src.core.agentverse.llms.base import BaseLLM
from src.core.agentverse.llms.mock import MockLLM
from src.core.agentverse.exceptions import ConfigError

LLM_TYPES: Dict[str, Type[BaseLLM]] = {
    "mock": MockLLM,
    # Add other LLM types here
}

def create_llm(config: Dict[str, Any]) -> BaseLLM:
    """Create LLM instance from config"""
    llm_type = config.get("type")
    if llm_type not in LLM_TYPES:
        raise ConfigError(f"Unknown LLM type: {llm_type}")
        
    return LLM_TYPES[llm_type](config)

__all__ = [
    "BaseLLM",
    "MockLLM",
    "create_llm"
] 