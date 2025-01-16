from typing import Dict, Type, Any
from src.core.agentverse.memory.base import BaseMemory

class MemoryRegistry:
    """Registry for memory components"""
    
    def __init__(self, *args, **kwargs):
        self._memories = {}
        self.name = "MemoryRegistry"
        
    def register(self, name: str, memory_class=None):
        """Register a new memory type. Can be used as a decorator or direct method."""
        def decorator(cls):
            if not issubclass(cls, BaseMemory):
                raise ValueError(f"Class {cls.__name__} must inherit from BaseMemory")
            self._memories[name] = cls
            return cls
            
        if memory_class is None:
            return decorator
            
        decorator(memory_class)
        return memory_class
        
    def get(self, name: str):
        """Get a memory component by name"""
        if name not in self._memories:
            raise KeyError(f"Memory '{name}' not found in registry")
        return self._memories[name]
    
    def build(self, name: str, **kwargs) -> BaseMemory:
        """Build a memory instance with given configuration"""
        if name not in self._memories:
            raise KeyError(f"Memory '{name}' not found in registry")
        return self._memories[name](**kwargs)
    
    def list_memories(self):
        """List all registered memories"""
        return list(self._memories.keys())

# Create singleton instance
memory_registry = MemoryRegistry() 