from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, ConfigDict
from abc import ABC, abstractmethod
import logging

from src.core.agentverse.memory.backends.base import BaseBackend
from src.core.agentverse.exceptions import BackendError

logger = logging.getLogger(__name__)

class HybridConfig(BaseModel):
    """Hybrid backend configuration"""
    backends: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    sync_operations: bool = True
    batch_size: int = 100
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class HybridBackend(BaseBackend, ABC):
    """Base class for hybrid storage backends"""
    
    def __init__(
        self,
        config: Optional[HybridConfig] = None,
        **kwargs
    ):
        """Initialize hybrid backend
        
        Args:
            config: Optional hybrid configuration
            **kwargs: Additional arguments
        """
        super().__init__()
        self.config = config or HybridConfig(**kwargs)
        self._backends = {}
    
    @abstractmethod
    async def initialize_backends(self) -> None:
        """Initialize all backends
        
        Raises:
            BackendError: If initialization fails
        """
        pass
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to all backends
        
        Raises:
            BackendError: If connection fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from all backends"""
        pass
    
    @abstractmethod
    async def store(
        self,
        data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Store data in backends
        
        Args:
            data: Data to store
            **kwargs: Additional arguments
            
        Returns:
            Storage results
            
        Raises:
            BackendError: If storage fails
        """
        pass
    
    @abstractmethod
    async def retrieve(
        self,
        query: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve data from backends
        
        Args:
            query: Query parameters
            **kwargs: Additional arguments
            
        Returns:
            Retrieved data
            
        Raises:
            BackendError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def delete(
        self,
        query: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Delete data from backends
        
        Args:
            query: Query parameters
            **kwargs: Additional arguments
            
        Returns:
            Deletion results
            
        Raises:
            BackendError: If deletion fails
        """
        pass
    
    @abstractmethod
    async def clear(self) -> Dict[str, bool]:
        """Clear all backends
        
        Returns:
            Clear results
            
        Raises:
            BackendError: If clear fails
        """
        pass
    
    async def _validate_backends(self) -> None:
        """Validate backend configuration
        
        Raises:
            BackendError: If validation fails
        """
        if not self._backends:
            raise BackendError(
                message="No backends configured"
            ) 