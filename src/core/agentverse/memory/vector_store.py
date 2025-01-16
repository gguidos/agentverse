from typing import List, Dict, Any, Optional, Union
import numpy as np
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
from src.core.agentverse.memory.base import BaseMemory, Message
import logging
from src.core.agentverse.memory.backends.base import VectorStorageBackend
from src.core.agentverse.memory.backends.memory import InMemoryVectorStorage
from src.core.agentverse.memory.backends.chroma import ChromaVectorStorage

logger = logging.getLogger(__name__)

class VectorStoreMemory(BaseMemory):
    def __init__(self, 
                 embedding_service,
                 backend: str = "memory",
                 backend_config: Dict[str, Any] = None):
        super().__init__()
        if embedding_service is None:
            raise ValueError("embedding_service cannot be None")
            
        self.embedding_service = embedding_service
        
        # Initialize storage backend
        backend_config = backend_config or {}
        if backend == "memory":
            self.storage = InMemoryVectorStorage()
        elif backend == "chroma":
            self.storage = ChromaVectorStorage(**backend_config)
        else:
            raise ValueError(f"Unknown backend: {backend}")
            
        logger.debug(f"VectorStoreMemory initialized with {backend} backend")

    def __repr__(self):
        return f"VectorStoreMemory(texts_count={len(self.texts)})"

    async def add_message(self, messages: List[Message]) -> None:
        """Add messages to memory"""
        texts = []
        vectors = []
        metadata_list = []
        
        for message in messages:
            embedding = await self.embedding_service.get_embedding(message.content)
            
            metadata = message.metadata.copy()
            metadata.update({
                "sender": message.sender,
                "timestamp": message.timestamp.isoformat() if message.timestamp else datetime.utcnow().isoformat(),
                "type": metadata.get('type', 'conversation')
            })
            
            texts.append(message.content)
            vectors.append(embedding)
            metadata_list.append(metadata)
            self.messages.append(message)
            
        await self.storage.add_vectors(texts, vectors, metadata_list)

    async def get_messages(self, 
                         start: int = 0, 
                         limit: int = 100,
                         filters: Dict = None) -> List[Message]:
        """Retrieve messages from memory"""
        filtered_messages = self.messages[start:start+limit]
        if filters:
            filtered_messages = [
                m for m in filtered_messages 
                if all(getattr(m, k, None) == v for k, v in filters.items())
            ]
        return filtered_messages

    async def get_similar_messages(self, query: str, limit: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get similar messages based on query"""
        try:
            logger.debug(f"Searching with query: {query} and filter: {metadata_filter}")
            
            # Get embedding for query
            query_embedding = await self.embedding_service.get_embedding(query)
            
            # Calculate similarities
            query_array = np.array(query_embedding).reshape(1, -1)
            vectors_array = np.array(self.vectors)
            similarities = cosine_similarity(query_array, vectors_array)[0]
            
            # Filter by metadata if specified
            filtered_indices = []
            for idx, meta in enumerate(self.metadata):
                if metadata_filter is None or all(meta.get(k) == v for k, v in metadata_filter.items()):
                    filtered_indices.append(idx)
            
            if not filtered_indices:
                return []
                
            # Get similarities for filtered indices
            filtered_similarities = [(idx, similarities[idx]) for idx in filtered_indices]
            
            # Sort by similarity
            sorted_results = sorted(filtered_similarities, key=lambda x: x[1], reverse=True)[:limit]
            
            results = []
            for idx, sim in sorted_results:
                results.append({
                    'text': self.texts[idx],
                    'similarity': float(sim),
                    'metadata': self.metadata[idx]
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting similar messages: {str(e)}", exc_info=True)
            return []
    
    def to_string(self) -> str:
        """Convert memory contents to string"""
        return "\n".join([f"{m.sender}: {m.content}" for m in self.messages])
    
    async def reset(self) -> None:
        """Clear all memory contents"""
        self.messages = []
        self.vectors = []
        self.texts = []
        self.metadata = []

    def __getstate__(self):
        """Custom state getter for serialization"""
        state = self.__dict__.copy()
        state.pop('embedding_service', None)
        return state

    def __setstate__(self, state):
        """Custom state setter for deserialization"""
        self.__dict__.update(state) 