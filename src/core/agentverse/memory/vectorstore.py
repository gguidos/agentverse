"""
Vector store service for memory management
"""

import logging
from typing import Any, Dict, List, Optional
import numpy as np
from chromadb import Client, Collection
from chromadb.config import Settings

from src.core.agentverse.exceptions import MemoryStorageError

logger = logging.getLogger(__name__)

class VectorstoreMemoryService:
    """Service for managing vector-based memory storage"""
    
    def __init__(
        self,
        collection_name: str,
        embedding_dim: int = 1536,  # Default for OpenAI embeddings
        host: str = "localhost",
        port: int = 8000,
        **kwargs
    ):
        """Initialize vector store
        
        Args:
            collection_name: Name of collection to use
            embedding_dim: Dimension of embeddings
            host: ChromaDB host
            port: ChromaDB port
            **kwargs: Additional configuration
        """
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim
        
        try:
            # Initialize ChromaDB client
            self.client = Client(Settings(
                chroma_api_impl="rest",
                chroma_server_host=host,
                chroma_server_http_port=port
            ))
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"dimension": embedding_dim}
            )
            
            logger.info(f"Initialized vector store: {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise MemoryStorageError(
                message="Vector store initialization failed",
                details={
                    "collection": collection_name,
                    "error": str(e)
                }
            )
    
    async def add_vectors(
        self,
        vectors: List[List[float]],
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """Add vectors to store
        
        Args:
            vectors: List of embedding vectors
            documents: List of original texts
            metadata: Optional metadata for each vector
            
        Returns:
            List of IDs for stored vectors
            
        Raises:
            MemoryStorageError: If storage fails
        """
        try:
            # Validate inputs
            if len(vectors) != len(documents):
                raise ValueError("Number of vectors and documents must match")
            
            if metadata and len(metadata) != len(vectors):
                raise ValueError("Number of metadata items must match vectors")
            
            # Add to collection
            ids = [f"vec_{i}" for i in range(len(vectors))]
            
            self.collection.add(
                embeddings=vectors,
                documents=documents,
                metadatas=metadata or [{}] * len(vectors),
                ids=ids
            )
            
            logger.debug(f"Added {len(vectors)} vectors to store")
            return ids
            
        except Exception as e:
            logger.error(f"Failed to add vectors: {e}")
            raise MemoryStorageError(
                message="Vector storage failed",
                details={"error": str(e)}
            )
    
    async def search_vectors(
        self,
        query_vector: List[float],
        k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors
        
        Args:
            query_vector: Query embedding
            k: Number of results to return
            threshold: Similarity threshold
            
        Returns:
            List of similar items with scores
            
        Raises:
            MemoryStorageError: If search fails
        """
        try:
            # Query collection
            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=k
            )
            
            # Format results
            matches = []
            for i, (doc, score) in enumerate(zip(
                results["documents"][0],
                results["distances"][0]
            )):
                if score >= threshold:
                    matches.append({
                        "document": doc,
                        "score": float(score),
                        "metadata": results["metadatas"][0][i]
                    })
            
            logger.debug(f"Found {len(matches)} matches above threshold")
            return matches
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise MemoryStorageError(
                message="Vector search failed",
                details={"error": str(e)}
            )
    
    async def clear(self) -> None:
        """Clear all vectors from store"""
        try:
            self.collection.delete()
            logger.info(f"Cleared vector store: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to clear vector store: {e}")
            raise MemoryStorageError(
                message="Vector store clear failed",
                details={"error": str(e)}
            ) 