from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict
from abc import ABC, abstractmethod
from datetime import datetime
import logging

from src.core.agentverse.memory.backends.base import BaseBackend
from src.core.agentverse.exceptions import BackendError

logger = logging.getLogger(__name__)

class DocumentConfig(BaseModel):
    """Document backend configuration"""
    collection: str = "memories"
    index_fields: List[str] = ["timestamp", "type"]
    batch_size: int = 100
    connection_url: Optional[str] = None
    
    model_config = ConfigDict(
        extra="allow"
    )

class DocumentBackend(BaseBackend, ABC):
    """Base class for document storage backends"""
    
    def __init__(
        self,
        config: Optional[DocumentConfig] = None,
        **kwargs
    ):
        """Initialize document backend
        
        Args:
            config: Optional document configuration
            **kwargs: Additional arguments
        """
        super().__init__()
        self.config = config or DocumentConfig(**kwargs)
        self._client = None
        self._collection = None
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to database
        
        Raises:
            BackendError: If connection fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from database"""
        pass
    
    @abstractmethod
    async def store(
        self,
        documents: List[Dict[str, Any]],
        **kwargs
    ) -> List[str]:
        """Store documents
        
        Args:
            documents: Documents to store
            **kwargs: Additional arguments
            
        Returns:
            List of document IDs
            
        Raises:
            BackendError: If storage fails
        """
        pass
    
    @abstractmethod
    async def retrieve(
        self,
        query: Dict[str, Any],
        limit: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Retrieve documents
        
        Args:
            query: Query filter
            limit: Optional result limit
            **kwargs: Additional arguments
            
        Returns:
            List of documents
            
        Raises:
            BackendError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def update(
        self,
        query: Dict[str, Any],
        update: Dict[str, Any],
        **kwargs
    ) -> int:
        """Update documents
        
        Args:
            query: Query filter
            update: Update operations
            **kwargs: Additional arguments
            
        Returns:
            Number of updated documents
            
        Raises:
            BackendError: If update fails
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        query: Dict[str, Any],
        **kwargs
    ) -> int:
        """Delete documents
        
        Args:
            query: Query filter
            **kwargs: Additional arguments
            
        Returns:
            Number of deleted documents
            
        Raises:
            BackendError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """Clear all documents
        
        Returns:
            Success status
            
        Raises:
            BackendError: If clear fails
        """
        pass
    
    async def _validate_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate documents
        
        Args:
            documents: Documents to validate
            
        Returns:
            Validated documents
            
        Raises:
            BackendError: If validation fails
        """
        try:
            validated = []
            
            for doc in documents:
                # Ensure dictionary
                if not isinstance(doc, dict):
                    raise BackendError(
                        message="Invalid document type",
                        details={"type": type(doc)}
                    )
                
                # Add timestamp if missing
                if "timestamp" not in doc:
                    doc["timestamp"] = datetime.utcnow()
                
                validated.append(doc)
            
            return validated
            
        except Exception as e:
            logger.error(f"Document validation failed: {str(e)}")
            raise BackendError(
                message=f"Failed to validate documents: {str(e)}"
            )
    
    async def _validate_query(
        self,
        query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate query
        
        Args:
            query: Query to validate
            
        Returns:
            Validated query
            
        Raises:
            BackendError: If validation fails
        """
        if not isinstance(query, dict):
            raise BackendError(
                message="Invalid query type",
                details={"type": type(query)}
            )
        return query 