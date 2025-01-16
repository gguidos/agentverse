"""
Vector Backend Module

This module provides vector storage and search functionality:
- FAISS backend
- Chroma backend
- Custom backends
"""

from typing import Dict, Type

from src.core.agentverse.memory.backends.vector.base import (
    VectorBackend,
    VectorBackendConfig
)
from src.core.agentverse.memory.backends.vector.faiss import FAISSBackend
from src.core.agentverse.memory.backends.vector.chroma import ChromaBackend

# Backend registry
VECTOR_BACKENDS: Dict[str, Type[VectorBackend]] = {
    "faiss": FAISSBackend,
    "chroma": ChromaBackend
}

def get_vector_backend(name: str) -> Type[VectorBackend]:
    """Get vector backend by name
    
    Args:
        name: Backend name
        
    Returns:
        Vector backend class
        
    Raises:
        ValueError: If backend not found
    """
    if name not in VECTOR_BACKENDS:
        raise ValueError(f"Vector backend not found: {name}")
    return VECTOR_BACKENDS[name]

__all__ = [
    'VectorBackend',
    'VectorBackendConfig',
    'FAISSBackend',
    'ChromaBackend',
    'get_vector_backend'
] 