from typing import Dict
from pydantic import BaseModel
from src.core.agentverse.memory.manipulators.base import BaseMemoryManipulator

class ManipulatorRegistry(BaseModel):
    """Registry for memory manipulators"""
    
    name: str = "ManipulatorRegistry"
    entries: Dict = {}
    
    def register(self, key: str):
        """Register a manipulator class"""
        def decorator(manipulator_class):
            if not issubclass(manipulator_class, BaseMemoryManipulator):
                raise ValueError(f"Class {manipulator_class.__name__} must inherit from BaseMemoryManipulator")
            self.entries[key] = manipulator_class
            return manipulator_class
        return decorator
    
    def get(self, key: str):
        """Get a registered manipulator"""
        if key not in self.entries:
            raise KeyError(f"Manipulator '{key}' not found")
        return self.entries[key]

# Create global registry instance
manipulator_registry = ManipulatorRegistry() 