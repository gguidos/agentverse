"""Environment Registry Module"""

from typing import Dict, Type, Any, Optional, List
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.visibility.base import BaseVisibility
from src.core.agentverse.environment.orders.base import BaseOrder

logger = logging.getLogger(__name__)

class RegistryConfig(BaseModel):
    """Configuration for registry"""
    allow_duplicates: bool = False
    validate_components: bool = True
    track_usage: bool = True

class RegistryEntry(BaseModel):
    """Information about registered component"""
    name: str
    description: str
    version: str
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    usage_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseRegistry:
    """Base registry for environment components"""
    
    def __init__(self, config: Optional[RegistryConfig] = None):
        self.config = config or RegistryConfig()
        self.entries: Dict[str, Any] = {}
        self.info: Dict[str, RegistryEntry] = {}
    
    def register(self, key: str, component: Any, **metadata) -> None:
        """Register a component"""
        if key in self.entries and not self.config.allow_duplicates:
            raise KeyError(f"Component '{key}' already registered")
            
        self.entries[key] = component
        self.info[key] = RegistryEntry(
            name=getattr(component, 'name', key),
            description=getattr(component, 'description', ''),
            version=getattr(component, 'version', '1.0.0'),
            metadata=metadata
        )
        
        logger.info(f"Registered component: {key}")
    
    def get(self, key: str) -> Any:
        """Get a registered component"""
        if key not in self.entries:
            raise KeyError(f"Component '{key}' not found")
            
        if self.config.track_usage:
            self.info[key].usage_count += 1
            
        return self.entries[key]
    
    def list_components(self) -> Dict[str, Dict[str, Any]]:
        """List all registered components"""
        return {
            key: {
                "name": info.name,
                "description": info.description,
                "version": info.version,
                "usage_count": info.usage_count,
                "metadata": info.metadata
            }
            for key, info in self.info.items()
        }

class EnvironmentRegistry(BaseRegistry):
    """Registry for environment types"""
    
    def register(self, key: str, env_class: Type[BaseEnvironment], **metadata) -> None:
        """Register environment class"""
        if not issubclass(env_class, BaseEnvironment):
            raise ValueError(f"Class {env_class.__name__} must inherit from BaseEnvironment")
        super().register(key, env_class, **metadata)

class VisibilityRegistry(BaseRegistry):
    """Registry for visibility handlers"""
    
    def register(self, key: str, visibility_class: Type[BaseVisibility], **metadata) -> None:
        """Register visibility class"""
        if not issubclass(visibility_class, BaseVisibility):
            raise ValueError(f"Class {visibility_class.__name__} must inherit from BaseVisibility")
        super().register(key, visibility_class, **metadata)

class OrderRegistry(BaseRegistry):
    """Registry for order types"""
    
    def register(self, key: str, order_class: Type[BaseOrder], **metadata) -> None:
        """Register order class"""
        if not issubclass(order_class, BaseOrder):
            raise ValueError(f"Class {order_class.__name__} must inherit from BaseOrder")
        super().register(key, order_class, **metadata)

# Create singleton instances
env_registry = EnvironmentRegistry()
visibility_registry = VisibilityRegistry()
order_registry = OrderRegistry()

__all__ = [
    'BaseRegistry',
    'EnvironmentRegistry',
    'VisibilityRegistry',
    'OrderRegistry',
    'env_registry',
    'visibility_registry',
    'order_registry'
] 