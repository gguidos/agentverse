"""Factory Registry Module"""

from typing import Dict, Any, Optional, Type
import logging

from src.core.agentverse.factories.base import BaseFactory

logger = logging.getLogger(__name__)

class FactoryRegistry:
    """Registry for managing factories"""
    
    def __init__(self):
        self.factories: Dict[str, BaseFactory] = {}
    
    def register(
        self,
        factory_type: str,
        factory: Type[BaseFactory]
    ) -> None:
        """Register a factory
        
        Args:
            factory_type: Type identifier for the factory
            factory: Factory class to register
        """
        self.factories[factory_type] = factory
        logger.info(f"Registered factory: {factory_type}")
    
    def get(
        self,
        factory_type: str
    ) -> Optional[Type[BaseFactory]]:
        """Get factory by type
        
        Args:
            factory_type: Type identifier for the factory
            
        Returns:
            Factory class if found, None otherwise
        """
        return self.factories.get(factory_type)
    
    def unregister(
        self,
        factory_type: str
    ) -> None:
        """Unregister a factory
        
        Args:
            factory_type: Type identifier for the factory
        """
        if factory_type in self.factories:
            del self.factories[factory_type]
            logger.info(f"Unregistered factory: {factory_type}") 