"""Base Factory Module"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar, Generic, Type
from pydantic import BaseModel

T = TypeVar('T')

class FactoryConfig(BaseModel):
    """Base factory configuration"""
    type: str
    name: Optional[str] = None
    metadata: Dict[str, Any] = {}

class BaseFactory(ABC, Generic[T]):
    """Base factory for creating objects"""
    
    @classmethod
    @abstractmethod
    async def create(
        cls,
        config: FactoryConfig,
        **kwargs
    ) -> T:
        """Create an instance
        
        Args:
            config: Factory configuration
            **kwargs: Additional creation options
            
        Returns:
            Created instance
        """
        pass
    
    @classmethod
    @abstractmethod
    async def validate_config(
        cls,
        config: FactoryConfig
    ) -> bool:
        """Validate factory configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @classmethod
    def get_defaults(cls) -> Dict[str, Any]:
        """Get default configuration
        
        Returns:
            Default configuration values
        """
        return {} 