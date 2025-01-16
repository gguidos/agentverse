from typing import Dict, Any, Optional, List, Union
import faiss
import numpy as np
import logging

from src.core.agentverse.memory.backends.vector.base import (
    VectorBackend,
    VectorBackendConfig
)
from src.core.agentverse.exceptions import VectorBackendError

logger = logging.getLogger(__name__)

class FAISSConfig(VectorBackendConfig):
    """FAISS configuration"""
    dimension: int
    index_type: str = "IndexFlatL2"
    nlist: int = 100  # For IVF indices
    nprobe: int = 10  # For IVF indices
    use_gpu: bool = False
    gpu_id: int = 0

class FAISSBackend(VectorBackend):
    """FAISS vector backend implementation"""
    
    def __init__(self, config: Optional[FAISSConfig] = None):
        """Initialize FAISS backend
        
        Args:
            config: Optional FAISS configuration
        """
        super().__init__(config or FAISSConfig())
        self.config: FAISSConfig = self.config
        self._index = None
        self._metadata: Dict[str, Dict[str, Any]] = {}
        
    async def connect(self) -> None:
        """Initialize FAISS index"""
        try:
            # Create index
            if self.config.index_type == "IndexFlatL2":
                self._index = faiss.IndexFlatL2(self.config.dimension)
            elif self.config.index_type == "IndexIVFFlat":
                quantizer = faiss.IndexFlatL2(self.config.dimension)
                self._index = faiss.IndexIVFFlat(
                    quantizer,
                    self.config.dimension,
                    self.config.nlist
                )
                self._index.nprobe = self.config.nprobe
            else:
                raise VectorBackendError(f"Unsupported index type: {self.config.index_type}")
            
            # Move to GPU if needed
            if self.config.use_gpu:
                res = faiss.StandardGpuResources()
                self._index = faiss.index_cpu_to_gpu(
                    res,
                    self.config.gpu_id,
                    self._index
                )
            
            logger.info(f"Initialized FAISS index: {self.config.index_type}")
            
        except Exception as e:
            logger.error(f"FAISS initialization failed: {str(e)}")
            raise VectorBackendError(f"Initialization failed: {str(e)}")
    
    async def add(
        self,
        vectors: Union[List[List[float]], np.ndarray],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        **kwargs
    ) -> List[str]:
        """Add vectors to FAISS
        
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
            # Validate inputs
            await self._validate_vectors(vectors)
            if metadata:
                await self._validate_metadata(metadata, len(vectors))
            
            # Convert to numpy array
            if isinstance(vectors, list):
                vectors = np.array(vectors)
            
            # Generate IDs if not provided
            if ids is None:
                ids = [str(i) for i in range(len(vectors))]
            
            # Add to FAISS
            self._index.add(vectors)
            
            # Store metadata
            if metadata:
                for i, id in enumerate(ids):
                    self._metadata[id] = metadata[i]
            
            return ids
            
        except Exception as e:
            logger.error(f"FAISS add failed: {str(e)}")
            raise VectorBackendError(f"Add failed: {str(e)}")
    
    async def search(
        self,
        query: Union[List[float], np.ndarray],
        k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search vectors in FAISS
        
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
            # Convert to numpy array
            if isinstance(query, list):
                query = np.array([query])
            elif isinstance(query, np.ndarray) and len(query.shape) == 1:
                query = query.reshape(1, -1)
            
            # Search in FAISS
            distances, indices = self._index.search(query, k)
            
            # Format results
            results = []
            for i in range(len(indices[0])):
                idx = indices[0][i]
                id = str(idx)
                result = {
                    'id': id,
                    'distance': float(distances[0][i])
                }
                
                # Add metadata if available
                if id in self._metadata:
                    result['metadata'] = self._metadata[id]
                
                # Apply filter if provided
                if filter and not self._matches_filter(result.get('metadata', {}), filter):
                    continue
                    
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"FAISS search failed: {str(e)}")
            raise VectorBackendError(f"Search failed: {str(e)}")
    
    async def delete(
        self,
        ids: Union[str, List[str]],
        **kwargs
    ) -> None:
        """Delete vectors from FAISS
        
        Note: FAISS does not support deletion. This is a no-op.
        """
        logger.warning("FAISS does not support deletion")
    
    async def clear(self, **kwargs) -> None:
        """Clear all vectors from FAISS
        
        Note: Reinitializes the index.
        """
        try:
            await self.connect()
            self._metadata.clear()
            
        except Exception as e:
            logger.error(f"FAISS clear failed: {str(e)}")
            raise VectorBackendError(f"Clear failed: {str(e)}")
    
    def _matches_filter(
        self,
        metadata: Dict[str, Any],
        filter: Dict[str, Any]
    ) -> bool:
        """Check if metadata matches filter
        
        Args:
            metadata: Vector metadata
            filter: Filter criteria
            
        Returns:
            True if matches, False otherwise
        """
        for key, value in filter.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True 