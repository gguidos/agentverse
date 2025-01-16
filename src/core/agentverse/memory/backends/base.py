from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
import logging

from src.core.agentverse.exceptions import (
    MemoryError,
    MemoryStorageError,
    MemoryRetrievalError
)

logger = logging.getLogger(__name__)

class BackendConfig(BaseModel):
    """Base configuration for memory backends"""
    name: str = "base"
    persistence: bool = True
    max_size: Optional[int] = None
    ttl: Optional[int] = None
    
    class Config:
        extra = "allow"

class BaseBackend(ABC):
    """Base class for memory backends"""
    
    def __init__(self, config: Optional[BackendConfig] = None):
        """Initialize memory backend
        
        Args:
            config: Optional backend configuration
        """
        self.config = config or BackendConfig()
    
    @abstractmethod
    async def store(
        self,
        key: str,
        data: Dict[str, Any],
        **kwargs
    ) -> None:
        """Store data in memory
        
        Args:
            key: Storage key
            data: Data to store
            **kwargs: Additional storage options
            
        Raises:
            MemoryStorageError: If storage fails
        """
        pass
    
    @abstractmethod
    async def retrieve(
        self,
        key: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Retrieve data from memory
        
        Args:
            key: Storage key
            **kwargs: Additional retrieval options
            
        Returns:
            Retrieved data if found, None otherwise
            
        Raises:
            MemoryRetrievalError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        key: str,
        **kwargs
    ) -> bool:
        """Delete data from memory
        
        Args:
            key: Storage key
            **kwargs: Additional deletion options
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            MemoryError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def clear(self, **kwargs) -> None:
        """Clear all data from memory
        
        Args:
            **kwargs: Additional clear options
            
        Raises:
            MemoryError: If clear fails
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: Union[str, Dict[str, Any]],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search memory
        
        Args:
            query: Search query
            **kwargs: Additional search options
            
        Returns:
            List of matching items
            
        Raises:
            MemoryError: If search fails
        """
        pass
    
    async def _validate_key(self, key: str) -> None:
        """Validate storage key
        
        Args:
            key: Key to validate
            
        Raises:
            ValueError: If key is invalid
        """
        if not isinstance(key, str) or not key:
            raise ValueError("Invalid storage key")
    
    async def _validate_data(self, data: Dict[str, Any]) -> None:
        """Validate data
        
        Args:
            data: Data to validate
            
        Raises:
            ValueError: If data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Invalid data format")
    
    async def _check_size_limit(self) -> None:
        """Check memory size limit
        
        Raises:
            MemoryError: If size limit exceeded
        """
        if self.config.max_size:
            # Implement size checking
            pass
    
    async def _enforce_ttl(self, key: str) -> None:
        """Enforce time-to-live
        
        Args:
            key: Storage key
            
        Raises:
            MemoryError: If TTL enforcement fails
        """
        if self.config.ttl:
            # Implement TTL enforcement
            pass 