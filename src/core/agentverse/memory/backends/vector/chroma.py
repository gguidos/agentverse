from typing import Dict, Any, Optional, List, Union
import chromadb
from chromadb.config import Settings
import logging
import numpy as np

from src.core.agentverse.memory.backends.vector.base import VectorBackend, VectorBackendConfig
from src.core.agentverse.exceptions import VectorBackendError

logger = logging.getLogger(__name__)

class ChromaConfig(VectorBackendConfig):
    """ChromaDB configuration"""
    host: Optional[str] = "localhost"
    port: Optional[int] = 8000
    persist_directory: Optional[str] = None
    collection_name: str = "agentverse"
    distance_func: str = "cosine"
    embedding_function: Optional[Any] = None

class ChromaBackend(VectorBackend):
    """ChromaDB vector backend implementation"""
    
    def __init__(self, config: Optional[ChromaConfig] = None):
        """Initialize ChromaDB backend
        
        Args:
            config: Optional ChromaDB configuration
        """
        super().__init__(config or ChromaConfig())
        self.config: ChromaConfig = self.config
        self._client = None
        self._collection = None
        
    async def connect(self) -> None:
        """Connect to ChromaDB"""
        try:
            # Initialize client
            settings = Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.config.persist_directory,
                anonymized_telemetry=False
            )
            
            self._client = chromadb.Client(settings)
            
            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.config.collection_name,
                embedding_function=self.config.embedding_function,
                metadata={"hnsw:space": self.config.distance_func}
            )
            
            logger.info(f"Connected to ChromaDB collection: {self.config.collection_name}")
            
        except Exception as e:
            logger.error(f"ChromaDB connection failed: {str(e)}")
            raise VectorBackendError(f"Connection failed: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from ChromaDB"""
        try:
            if self._client:
                self._client = None
                self._collection = None
                
        except Exception as e:
            logger.error(f"ChromaDB disconnect failed: {str(e)}")
            raise VectorBackendError(f"Disconnect failed: {str(e)}")
    
    async def add(
        self,
        vectors: Union[List[List[float]], np.ndarray],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        **kwargs
    ) -> List[str]:
        """Add vectors to ChromaDB
        
        Args:
            vectors: Vectors to add
            metadata: Optional metadata for vectors
            ids: Optional vector IDs
            **kwargs: Additional options
            
        Returns:
            List of vector IDs
            
        Raises:
            VectorBackendError: If add fails
        """
        try:
            # Validate connection
            if not self._collection:
                raise VectorBackendError("Not connected to ChromaDB")
                
            # Convert numpy array to list
            if isinstance(vectors, np.ndarray):
                vectors = vectors.tolist()
                
            # Add vectors
            self._collection.add(
                embeddings=vectors,
                metadatas=metadata,
                ids=ids,
                **kwargs
            )
            
            return ids or [str(i) for i in range(len(vectors))]
            
        except Exception as e:
            logger.error(f"ChromaDB add failed: {str(e)}")
            raise VectorBackendError(f"Add failed: {str(e)}")
    
    async def search(
        self,
        query: Union[List[float], np.ndarray],
        k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search vectors in ChromaDB
        
        Args:
            query: Query vector
            k: Number of results
            filter: Optional metadata filter
            **kwargs: Additional options
            
        Returns:
            List of search results
            
        Raises:
            VectorBackendError: If search fails
        """
        try:
            # Validate connection
            if not self._collection:
                raise VectorBackendError("Not connected to ChromaDB")
                
            # Convert numpy array to list
            if isinstance(query, np.ndarray):
                query = query.tolist()
                
            # Search vectors
            results = self._collection.query(
                query_embeddings=[query],
                n_results=k,
                where=filter,
                **kwargs
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i]
                })
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"ChromaDB search failed: {str(e)}")
            raise VectorBackendError(f"Search failed: {str(e)}")
    
    async def delete(
        self,
        ids: Union[str, List[str]],
        **kwargs
    ) -> None:
        """Delete vectors from ChromaDB
        
        Args:
            ids: Vector ID(s) to delete
            **kwargs: Additional options
            
        Raises:
            VectorBackendError: If deletion fails
        """
        try:
            # Validate connection
            if not self._collection:
                raise VectorBackendError("Not connected to ChromaDB")
                
            # Convert single ID to list
            if isinstance(ids, str):
                ids = [ids]
                
            # Delete vectors
            self._collection.delete(
                ids=ids,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"ChromaDB delete failed: {str(e)}")
            raise VectorBackendError(f"Delete failed: {str(e)}")
    
    async def clear(self, **kwargs) -> None:
        """Clear all vectors from ChromaDB
        
        Args:
            **kwargs: Additional options
            
        Raises:
            VectorBackendError: If clear fails
        """
        try:
            # Validate connection
            if not self._collection:
                raise VectorBackendError("Not connected to ChromaDB")
                
            # Delete collection
            self._client.delete_collection(self.config.collection_name)
            
            # Recreate collection
            self._collection = self._client.create_collection(
                name=self.config.collection_name,
                embedding_function=self.config.embedding_function,
                metadata={"hnsw:space": self.config.distance_func}
            )
            
        except Exception as e:
            logger.error(f"ChromaDB clear failed: {str(e)}")
            raise VectorBackendError(f"Clear failed: {str(e)}") 