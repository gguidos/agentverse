from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
import numpy as np
from pydantic import BaseModel, Field

from src.core.agentverse.memory.backends.base import BaseBackend, BackendConfig
from src.core.agentverse.exceptions import VectorBackendError

class VectorBackendConfig(BackendConfig):
    """Vector backend configuration"""
    dimension: Optional[int] = None
    metric: str = "cosine"
    batch_size: int = 1000
    normalize: bool = True
    cache_size: Optional[int] = None
    
    class Config:
        extra = "allow"

class VectorBackend(BaseBackend, ABC):
    """Base class for vector backends"""
    
    def __init__(self, config: Optional[VectorBackendConfig] = None):
        """Initialize vector backend
        
        Args:
            config: Optional vector backend configuration
        """
        super().__init__(config or VectorBackendConfig())
        self.config: VectorBackendConfig = self.config
    
    @abstractmethod
    async def add(
        self,
        vectors: Union[List[List[float]], np.ndarray],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        **kwargs
    ) -> List[str]:
        """Add vectors to backend
        
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
        pass
    
    @abstractmethod
    async def search(
        self,
        query: Union[List[float], np.ndarray],
        k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search vectors in backend
        
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
        pass
    
    @abstractmethod
    async def delete(
        self,
        ids: Union[str, List[str]],
        **kwargs
    ) -> None:
        """Delete vectors from backend
        
        Args:
            ids: Vector ID(s) to delete
            **kwargs: Additional options
            
        Raises:
            VectorBackendError: If deletion fails
        """
        pass
    
    async def _validate_vectors(
        self,
        vectors: Union[List[List[float]], np.ndarray]
    ) -> None:
        """Validate vector data
        
        Args:
            vectors: Vectors to validate
            
        Raises:
            ValueError: If vectors are invalid
        """
        try:
            # Convert to numpy array for validation
            if isinstance(vectors, list):
                vectors = np.array(vectors)
                
            # Check dimensions
            if self.config.dimension and vectors.shape[1] != self.config.dimension:
                raise ValueError(
                    f"Invalid vector dimension: {vectors.shape[1]}, "
                    f"expected {self.config.dimension}"
                )
                
            # Check for NaN/Inf
            if not np.all(np.isfinite(vectors)):
                raise ValueError("Vectors contain NaN or Inf values")
                
            # Normalize if needed
            if self.config.normalize:
                vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
                
        except Exception as e:
            raise ValueError(f"Vector validation failed: {str(e)}")
    
    async def _validate_metadata(
        self,
        metadata: List[Dict[str, Any]],
        count: int
    ) -> None:
        """Validate metadata
        
        Args:
            metadata: Metadata to validate
            count: Expected number of items
            
        Raises:
            ValueError: If metadata is invalid
        """
        if metadata is not None:
            if not isinstance(metadata, list):
                raise ValueError("Metadata must be a list")
                
            if len(metadata) != count:
                raise ValueError(
                    f"Metadata length {len(metadata)} does not match "
                    f"vector count {count}"
                )
                
            if not all(isinstance(m, dict) for m in metadata):
                raise ValueError("Metadata items must be dictionaries")
    
    async def _validate_ids(
        self,
        ids: List[str],
        count: int
    ) -> None:
        """Validate vector IDs
        
        Args:
            ids: IDs to validate
            count: Expected number of items
            
        Raises:
            ValueError: If IDs are invalid
        """
        if ids is not None:
            if not isinstance(ids, list):
                raise ValueError("IDs must be a list")
                
            if len(ids) != count:
                raise ValueError(
                    f"ID count {len(ids)} does not match "
                    f"vector count {count}"
                )
                
            if not all(isinstance(id, str) for id in ids):
                raise ValueError("IDs must be strings")
                
            if len(set(ids)) != len(ids):
                raise ValueError("Duplicate IDs found") 