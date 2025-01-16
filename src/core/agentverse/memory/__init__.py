"""
Memory Module

This module provides memory management for agents:

1. Memory Types:
   - Vector Memory: For similarity search
   - Document Memory: For structured data
   - Cache Memory: For fast access

2. Memory Features:
   - Storage/Retrieval
   - Search/Query
   - Persistence
   - Indexing
"""

from typing import Dict, Type, Optional, Any

from src.core.agentverse.memory.base import BaseMemory, MemoryConfig
from src.core.agentverse.memory.backends import (
    BaseBackend,
    VectorBackend,
    FAISSBackend,
    ChromaBackend,
    get_backend
)
from src.core.agentverse.memory.manipulators import (
    BaseManipulator,
    VectorManipulator,
    DocumentManipulator
)

# Memory type registry
MEMORY_TYPES = {
    "vector": {
        "faiss": FAISSBackend,
        "chroma": ChromaBackend
    }
}

def get_memory(
    memory_type: str,
    backend_name: str,
    config: Optional[Dict[str, Any]] = None
) -> BaseMemory:
    """Get memory instance
    
    Args:
        memory_type: Type of memory (vector, document, cache)
        backend_name: Name of backend implementation
        config: Optional configuration
        
    Returns:
        Memory instance
        
    Raises:
        ValueError: If memory type or backend not found
    """
    if memory_type not in MEMORY_TYPES:
        raise ValueError(f"Memory type not found: {memory_type}")
        
    backends = MEMORY_TYPES[memory_type]
    if backend_name not in backends:
        raise ValueError(f"Backend not found: {backend_name}")
        
    backend_class = backends[backend_name]
    backend = backend_class(config)
    
    # Create appropriate manipulator
    if memory_type == "vector":
        manipulator = VectorManipulator()
    else:
        manipulator = DocumentManipulator()
    
    return BaseMemory(
        backend=backend,
        manipulator=manipulator,
        config=config
    )

__all__ = [
    'BaseMemory',
    'MemoryConfig',
    'BaseBackend',
    'VectorBackend',
    'FAISSBackend',
    'ChromaBackend',
    'BaseManipulator',
    'VectorManipulator',
    'DocumentManipulator',
    'get_memory',
    'get_backend'
]

# Version
__version__ = "1.0.0" 