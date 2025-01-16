from typing import Dict, Type, Any
from src.core.agentverse.llm.base import BaseLLM

class LLMRegistry:
    """Registry for LLM models"""
    
    def __init__(self, *args, **kwargs):
        self._llms = {}
        self.name = "LLMRegistry"
        
    def register(self, *names: str):
        """Register a new LLM type with multiple names. Can be used as a decorator."""
        def decorator(cls):
            if not issubclass(cls, BaseLLM):
                raise ValueError(f"Class {cls.__name__} must inherit from BaseLLM")
            for name in names:
                if name in self._llms:
                    raise KeyError(f"LLM '{name}' already registered")
                self._llms[name] = cls
            return cls
        return decorator
        
    def get(self, name: str) -> Type[BaseLLM]:
        """Get an LLM by name"""
        if name not in self._llms:
            raise KeyError(f"LLM '{name}' not found in registry")
        return self._llms[name]
    
    def build(self, name: str, **kwargs) -> BaseLLM:
        """Build an LLM instance with given configuration"""
        llm_class = self.get(name)
        return llm_class(**kwargs)
    
    def list_llms(self) -> list:
        """List all registered LLMs"""
        return list(self._llms.keys())
    
    def __contains__(self, name: str) -> bool:
        """Check if LLM is registered"""
        return name in self._llms

# Create singleton instance
llm_registry = LLMRegistry()

# Example usage:
"""
@llm_registry.register("gpt-3.5", "gpt-3.5-turbo")
class GPT35ChatModel(BaseChatModel):
    pass

# Get model class
model_class = llm_registry.get("gpt-3.5")

# Build model instance
model = llm_registry.build("gpt-3.5", 
    config=LLMConfig(temperature=0.8)
)
""" 