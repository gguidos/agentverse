from typing import Dict, Any, Optional, List, Union
import numpy as np
import logging

from src.core.agentverse.memory.backends.hybrid.base import (
    HybridBackend,
    HybridConfig
)
from src.core.agentverse.memory.backends.vector import VectorBackend
from src.core.agentverse.memory.backends.document import DocumentBackend
from src.core.agentverse.exceptions import BackendError

logger = logging.getLogger(__name__)

class VectorDocumentConfig(HybridConfig):
    """Vector-document backend configuration"""
    vector_backend: Dict[str, Any] = Field(default_factory=dict)
    document_backend: Dict[str, Any] = Field(default_factory=dict)
    id_field: str = "id"
    vector_field: str = "vector"
    metadata_field: str = "metadata"

class VectorDocumentBackend(HybridBackend):
    """Combined vector and document storage backend"""
    
    def __init__(self, *args, **kwargs):
        """Initialize vector-document backend"""
        super().__init__(*args, **kwargs)
        self.config: VectorDocumentConfig = (
            self.config 
            if isinstance(self.config, VectorDocumentConfig)
            else VectorDocumentConfig(**self.config.model_dump())
        )
    
    async def initialize_backends(self) -> None:
        """Initialize vector and document backends"""
        try:
            # Initialize vector backend
            vector_class = self.config.vector_backend.pop("class", None)
            if not vector_class or not issubclass(vector_class, VectorBackend):
                raise BackendError(
                    message="Invalid vector backend class"
                )
            self._backends["vector"] = vector_class(
                **self.config.vector_backend
            )
            
            # Initialize document backend
            doc_class = self.config.document_backend.pop("class", None)
            if not doc_class or not issubclass(doc_class, DocumentBackend):
                raise BackendError(
                    message="Invalid document backend class"
                )
            self._backends["document"] = doc_class(
                **self.config.document_backend
            )
            
        except Exception as e:
            logger.error(f"Backend initialization failed: {str(e)}")
            raise BackendError(
                message=f"Failed to initialize backends: {str(e)}"
            )
    
    async def connect(self) -> None:
        """Connect to both backends"""
        try:
            await self._validate_backends()
            
            # Connect to vector backend
            await self._backends["vector"].connect()
            
            # Connect to document backend
            await self._backends["document"].connect()
            
        except Exception as e:
            logger.error(f"Backend connection failed: {str(e)}")
            raise BackendError(
                message=f"Failed to connect to backends: {str(e)}"
            )
    
    async def disconnect(self) -> None:
        """Disconnect from both backends"""
        try:
            if "vector" in self._backends:
                await self._backends["vector"].disconnect()
            
            if "document" in self._backends:
                await self._backends["document"].disconnect()
                
        except Exception as e:
            logger.error(f"Backend disconnection failed: {str(e)}")
    
    async def store(
        self,
        data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Store data in both backends
        
        Args:
            data: Data containing vectors and documents
            **kwargs: Additional arguments
            
        Returns:
            Storage results
        """
        try:
            await self._validate_backends()
            
            results = {}
            
            # Store vectors
            if self.config.vector_field in data:
                vector_ids = await self._backends["vector"].store(
                    vectors=data[self.config.vector_field],
                    metadata=data.get(self.config.metadata_field),
                    **kwargs
                )
                results["vector_ids"] = vector_ids
            
            # Store documents
            if self.config.metadata_field in data:
                doc_ids = await self._backends["document"].store(
                    documents=data[self.config.metadata_field],
                    **kwargs
                )
                results["document_ids"] = doc_ids
            
            return results
            
        except Exception as e:
            logger.error(f"Hybrid storage failed: {str(e)}")
            raise BackendError(
                message=f"Failed to store data: {str(e)}"
            )
    
    async def retrieve(
        self,
        query: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve data from both backends
        
        Args:
            query: Query parameters
            **kwargs: Additional arguments
            
        Returns:
            Retrieved data
        """
        try:
            await self._validate_backends()
            
            results = {}
            
            # Vector similarity search
            if "vector" in query:
                vector_results = await self._backends["vector"].search(
                    query=query["vector"],
                    k=query.get("k", 5),
                    **kwargs
                )
                results["vector_results"] = vector_results
            
            # Document query
            if "filter" in query:
                doc_results = await self._backends["document"].retrieve(
                    query=query["filter"],
                    limit=query.get("limit"),
                    **kwargs
                )
                results["document_results"] = doc_results
            
            return results
            
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {str(e)}")
            raise BackendError(
                message=f"Failed to retrieve data: {str(e)}"
            )
    
    async def delete(
        self,
        query: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Delete data from both backends
        
        Args:
            query: Query parameters
            **kwargs: Additional arguments
            
        Returns:
            Deletion results
        """
        try:
            await self._validate_backends()
            
            results = {}
            
            # Delete vectors
            if "vector_ids" in query:
                vector_result = await self._backends["vector"].delete(
                    ids=query["vector_ids"],
                    **kwargs
                )
                results["vector_deleted"] = vector_result
            
            # Delete documents
            if "filter" in query:
                doc_result = await self._backends["document"].delete(
                    query=query["filter"],
                    **kwargs
                )
                results["documents_deleted"] = doc_result
            
            return results
            
        except Exception as e:
            logger.error(f"Hybrid deletion failed: {str(e)}")
            raise BackendError(
                message=f"Failed to delete data: {str(e)}"
            )
    
    async def clear(self) -> Dict[str, bool]:
        """Clear both backends
        
        Returns:
            Clear results
        """
        try:
            await self._validate_backends()
            
            results = {}
            
            # Clear vector backend
            results["vector_cleared"] = await self._backends["vector"].clear()
            
            # Clear document backend
            results["document_cleared"] = await self._backends["document"].clear()
            
            return results
            
        except Exception as e:
            logger.error(f"Hybrid clear failed: {str(e)}") 