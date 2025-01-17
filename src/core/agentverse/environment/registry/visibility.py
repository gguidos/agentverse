"""Visibility Registry Module"""

from typing import Type
from src.core.agentverse.environment.registry.base import BaseRegistry
from src.core.agentverse.environment.visibility.base import BaseVisibility

class VisibilityRegistry(BaseRegistry):
    """Registry for visibility handlers"""
    
    def register(self, key: str, visibility_class: Type[BaseVisibility], **metadata) -> None:
        """Register visibility class"""
        if not issubclass(visibility_class, BaseVisibility):
            raise ValueError(f"Class {visibility_class.__name__} must inherit from BaseVisibility")
        super().register(key, visibility_class, **metadata)

# Create singleton instance
visibility_registry = VisibilityRegistry() 