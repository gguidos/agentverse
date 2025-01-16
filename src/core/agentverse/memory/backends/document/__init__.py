"""
Document Backend Module

This module provides document storage implementations for memory backends:
- MongoDB: Document database
- PostgreSQL: Relational database
- Redis: In-memory store

Key Features:
1. Document storage
2. Query operations
3. Indexing
4. Schema management
5. Persistence
"""

from src.core.agentverse.memory.backends.document.base import DocumentBackend
from src.core.agentverse.memory.backends.document.mongo import MongoBackend

__all__ = [
    'DocumentBackend',
    'MongoBackend'
] 