"""
AgentVerse Backends Module

This module provides backend implementations for different services and functionalities:

1. LLM Backends:
   - OpenAI GPT
   - Azure OpenAI
   - Anthropic Claude
   - Local LLMs

2. Vector Store Backends:
   - FAISS
   - Chroma
   - Pinecone
   - Milvus

3. Cache Backends:
   - Redis
   - In-memory
   - File-based
   - Distributed

4. Storage Backends:
   - SQLite
   - PostgreSQL
   - MongoDB
   - File System

Key Components:
- BaseBackend: Abstract base class for all backends
- LLMBackend: Base class for LLM implementations
- VectorBackend: Base class for vector stores
- CacheBackend: Base class for caching systems
- StorageBackend: Base class for storage systems

Example:
    ```python
    from src.core.agentverse.backends import OpenAIBackend
    
    # Create backend instance
    backend = OpenAIBackend(
        api_key="your-api-key",
        model="gpt-4"
    )
    
    # Generate response
    response = await backend.generate(
        prompt="Your prompt here",
        temperature=0.7
    )
    ```

Backend Configuration:
Each backend can be configured through environment variables or config files:

```yaml
backends:
  llm:
    type: openai
    api_key: ${OPENAI_API_KEY}
    model: gpt-4
  vector:
    type: faiss
    dimension: 768
    metric: cosine
  cache:
    type: redis
    url: ${REDIS_URL}
  storage:
    type: postgresql
    url: ${DATABASE_URL}
```
"""

from src.core.agentverse.backends.base import BaseBackend
from src.core.agentverse.backends.llm import LLMBackend
from src.core.agentverse.backends.vector import VectorBackend
from src.core.agentverse.backends.cache import CacheBackend
from src.core.agentverse.backends.storage import StorageBackend

__all__ = [
    'BaseBackend',
    'LLMBackend',
    'VectorBackend',
    'CacheBackend',
    'StorageBackend'
]

# Version
__version__ = "1.1.0" 