"""
AgentVerse LLM Module

This module provides language model integrations and abstractions.
"""

import logging
from typing import Dict, Type

from src.core.agentverse.llm.base import BaseLLM
from src.core.agentverse.llm.openai import OpenAILLM

logger = logging.getLogger(__name__)

# Registry of available LLM implementations
LLM_REGISTRY: Dict[str, Type[BaseLLM]] = {
    "gpt-3.5-turbo": OpenAILLM,
    "gpt-4": OpenAILLM,
    "gpt-4-turbo": OpenAILLM
}

def create_llm(
    model_name: str,
    api_key: str,
    **kwargs
) -> BaseLLM:
    """Create LLM instance
    
    Args:
        model_name: Name of model to use
        api_key: API key for service
        **kwargs: Additional model parameters
        
    Returns:
        Configured LLM instance
        
    Raises:
        ValueError: If model not found
    """
    if model_name not in LLM_REGISTRY:
        raise ValueError(f"Unknown model: {model_name}")
        
    llm_class = LLM_REGISTRY[model_name]
    return llm_class(
        model=model_name,
        api_key=api_key,
        **kwargs
    )

__all__ = [
    "BaseLLM",
    "OpenAILLM",
    "create_llm",
    "LLM_REGISTRY"
] 