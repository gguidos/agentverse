"""
AgentVerse LLM Services Module

This module provides Language Model (LLM) services with different provider implementations.
It includes base classes and concrete implementations for various LLM providers,
supporting text generation, embeddings, and evaluation capabilities.

Key Components:
    - Base Classes: Abstract base classes for LLM services
    - OpenAI Implementation: Service implementation for OpenAI models
    - Anthropic Implementation: Service implementation for Anthropic Claude
    - Configuration: Configuration settings for different LLM providers

Available Services:
    - OpenAIService: Service for GPT models
    - AnthropicService: Service for Claude models

Example Usage:
    >>> from src.core.agentverse.services.llm import OpenAIService, OpenAIConfig
    >>> 
    >>> # Configure and initialize service
    >>> config = OpenAIConfig(
    ...     api_key="your-api-key",
    ...     model="gpt-4"
    ... )
    >>> llm_service = OpenAIService(config)
    >>> 
    >>> # Generate text
    >>> response = await llm_service.generate("Tell me a joke")
    >>> 
    >>> # Get embeddings
    >>> embeddings = await llm_service.get_embeddings("Hello, world!")
"""

from src.core.agentverse.services.llm.base import (
    BaseLLMService,
    LLMConfig,
    LLMResponse
)

from src.core.agentverse.services.llm.openai import (
    OpenAIService,
    OpenAIConfig
)

from src.core.agentverse.services.llm.anthropic import (
    AnthropicService,
    AnthropicConfig
)

__all__ = [
    # Base classes
    "BaseLLMService",
    "LLMConfig",
    "LLMResponse",
    
    # OpenAI implementation
    "OpenAIService",
    "OpenAIConfig",
    
    # Anthropic implementation
    "AnthropicService",
    "AnthropicConfig"
] 