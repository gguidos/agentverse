"""Base Registry Module"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime

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