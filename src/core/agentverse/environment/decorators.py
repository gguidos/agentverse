"""Environment Decorators Module"""

from typing import Type, Any, Callable, TypeVar, Dict
import functools

T = TypeVar('T')

def component_decorator(registry_key: str) -> Callable[[Type[T]], Type[T]]:
    """Create a component registration decorator
    
    Args:
        registry_key: Key prefix for registry (e.g., "visibility", "order")
        
    Returns:
        Decorator function
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Store registration info on the class for later
        cls._registry_info = {
            "key": registry_key,
            "name": getattr(cls, "name", cls.__name__),
            "version": getattr(cls, "version", "1.0.0"),
            "description": getattr(cls, "description", "")
        }
        return cls
    return decorator

# Create specific decorators
visibility = component_decorator("visibility")
order = component_decorator("order")
environment = component_decorator("environment") 