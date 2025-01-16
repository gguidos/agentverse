"""
Hybrid Backend Module

This module provides hybrid storage implementations combining multiple backend types:
- VectorDocument: Combined vector and document storage
- CachedVector: Vector storage with caching
- DistributedHybrid: Distributed hybrid storage

Key Features:
1. Combined storage types
2. Coordinated operations
3. Consistent state
4. Performance optimization
5. Flexible configuration
"""

from src.core.agentverse.memory.backends.hybrid.base import HybridBackend
from src.core.agentverse.memory.backends.hybrid.vector_doc import VectorDocumentBackend
from src.core.agentverse.memory.backends.hybrid.cached import CachedVectorBackend

__all__ = [
    'HybridBackend',
    'VectorDocumentBackend',
    'CachedVectorBackend'
] 