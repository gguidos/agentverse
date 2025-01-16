from typing import List, Dict, Any, Optional
import uuid
import chromadb
from chromadb.config import Settings
from src.core.agentverse.memory.backends.base import VectorStorageBackend
from src.core.infrastructure.circuit_breaker import circuit_breaker
import logging

logger = logging.getLogger(__name__)

class ChromaVectorStorage(VectorStorageBackend):
    """ChromaDB-backed vector storage"""
    
    def __init__(self, persist_directory: str = "chroma_db"):
        self._client = chromadb.Client(
            Settings(
                persist_directory=persist_directory,
                is_persistent=True
            )
        )
        self._collection = self._client.get_or_create_collection(
            name=f"vectors_{uuid.uuid4().hex[:8]}",
            metadata={"hnsw:space": "cosine"}
        )
        
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    async def add_vectors(self, texts: List[str], vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> None:
        try:
            ids = [str(uuid.uuid4()) for _ in texts]
            self._collection.add(
                documents=texts,
                embeddings=vectors,
                metadatas=metadata,
                ids=ids
            )
        except Exception as e:
            logger.error(f"Failed to add vectors: {str(e)}")
            raise
        
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    async def search_vectors(self, query_vector: List[float], limit: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict[str, Any]]:
        try:
            results = self._collection.query(
                query_embeddings=[query_vector],
                n_results=limit,
                where=filter_dict
            )
            
            if not results['documents']:
                return []
                
            return [
                {
                    'text': doc,
                    'similarity': float(score),
                    'metadata': meta
                }
                for doc, score, meta in zip(
                    results['documents'][0],
                    results['distances'][0],
                    results['metadatas'][0]
                )
            ]
        except Exception as e:
            logger.error(f"Vector search failed: {str(e)}")
            raise
        
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    async def clear(self) -> None:
        try:
            self._collection.delete(where={})
        except Exception as e:
            logger.error(f"Failed to clear vectors: {str(e)}")
            raise

    async def health_check(self) -> bool:
        """Check if ChromaDB is responsive"""
        try:
            # Try a simple operation
            self._collection.count()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False 