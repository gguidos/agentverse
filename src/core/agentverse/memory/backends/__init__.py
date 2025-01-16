"""
Memory Backends Module

This module provides different memory storage implementations:

1. Vector Backends:
   - FAISS
   - Chroma
   - Custom vector stores

2. Document Backends:
   - MongoDB
   - SQLite
   - File system

3. Cache Backends:
   - Redis
   - In-memory
   - Local storage
"""

from typing import Dict, Type, Optional, Any

from src.core.agentverse.memory.backends.base import BaseBackend, BackendConfig
from src.core.agentverse.memory.backends.vector.base import (
    VectorBackend,
    VectorBackendConfig  # Updated from VectorConfig
)
from src.core.agentverse.memory.backends.vector import (
    FAISSBackend,
    ChromaBackend,
    get_vector_backend
)

# Backend type registry
BACKEND_TYPES = {
    "vector": {
        "faiss": FAISSBackend,
        "chroma": ChromaBackend
    }
}

def get_backend(
    backend_type: str,
    backend_name: str,
    config: Optional[Dict[str, Any]] = None
) -> BaseBackend:
    """Get memory backend instance
    
    Args:
        backend_type: Type of backend (vector, document, cache)
        backend_name: Name of specific backend implementation
        config: Optional backend configuration
        
    Returns:
        Backend instance
        
    Raises:
        ValueError: If backend type or name not found
    """
    if backend_type not in BACKEND_TYPES:
        raise ValueError(f"Backend type not found: {backend_type}")
        
    backends = BACKEND_TYPES[backend_type]
    if backend_name not in backends:
        raise ValueError(f"Backend not found: {backend_name}")
        
    backend_class = backends[backend_name]
    
    if config:
        if backend_type == "vector":
            config = VectorBackendConfig(**config)
        else:
            config = BackendConfig(**config)
            
    return backend_class(config)

__all__ = [
    'BaseBackend',
    'BackendConfig',
    'VectorBackend',
    'VectorBackendConfig',
    'FAISSBackend',
    'ChromaBackend',
    'get_backend'
]

# Version
__version__ = "1.1.0" 