"""
AgentVerse Embedding Services Module

This module provides functionality for generating text embeddings using various services.
It includes base classes and implementations for different embedding providers,
with a focus on AWS Bedrock embeddings.

Key Components:
    - Base Classes: Abstract base classes for embedding services
    - AWS Implementation: Concrete implementation for AWS Bedrock embeddings
    - Configuration: Configuration settings for embedding services

Example Usage:
    >>> from src.core.agentverse.services.embedding import get_embeddings_service, EmbeddingConfig
    >>> 
    >>> # Configure and get embedding service
    >>> config = EmbeddingConfig(model_name="amazon.titan-embed-text-v1", dimension=1536)
    >>> embedding_service = get_embeddings_service(config)
    >>> 
    >>> # Get embeddings
    >>> embedding = await embedding_service.get_embedding("Hello, world!")
    >>> embeddings = await embedding_service.get_embeddings(["Text 1", "Text 2"])
"""

from src.core.agentverse.services.embedding.base import (
    BaseEmbeddingService,
    EmbeddingConfig
)

from src.core.agentverse.services.embedding.aws import (
    AWSEmbeddingService,
    get_embeddings_service
)

__all__ = [
    # Base classes
    "BaseEmbeddingService",
    "EmbeddingConfig",
    
    # AWS implementation
    "AWSEmbeddingService",
    "get_embeddings_service"
] 