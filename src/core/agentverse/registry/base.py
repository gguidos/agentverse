from typing import Dict, Any, Type, Optional, ClassVar, List, TypeVar, Generic, Callable
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging
from functools import wraps

from src.core.agentverse.exceptions import RegistrationError

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RegistryItem(BaseModel):
    """Base model for registry items"""
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    registration_time: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        extra="allow"
    )

class Registry(Generic[T]):
    """Base registry for components
    
    Generic Args:
        T: Type of registered components
    """
    
    name: ClassVar[str] = "base_registry"
    description: ClassVar[str] = "Base component registry"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        name: str,
        validate_components: bool = True,
        track_metrics: bool = True
    ):
        """Initialize registry
        
        Args:
            name: Registry name
            validate_components: Whether to validate components
            track_metrics: Whether to track metrics
        """
        self._name = name
        self._registry: Dict[str, Type[T]] = {}
        self._items: Dict[str, RegistryItem] = {}
        self.validate_components = validate_components
        self.track_metrics = track_metrics
        self.registration_count = 0
        logger.info(f"Initialized {self._name} registry v{self.version}")
    
    def register(
        self,
        name: str,
        description: Optional[str] = None,
        version: str = "1.0.0",
        metadata: Optional[Dict[str, Any]] = None,
        component: Optional[Type[T]] = None
    ) -> Callable[[Type[T]], Type[T]]:
        """Register a component
        
        Can be used as decorator or direct method.
        
        Args:
            name: Component name
            description: Optional description
            version: Component version
            metadata: Optional metadata
            component: Optional component to register directly
            
        Returns:
            Registration decorator
            
        Raises:
            RegistrationError: If registration fails
        """
        def decorator(comp: Type[T]) -> Type[T]:
            try:
                # Validate component if configured
                if self.validate_components:
                    self._validate_component(comp)
                
                # Register component
                if name in self._registry:
                    logger.warning(f"Overwriting existing component '{name}'")
                
                self._registry[name] = comp
                
                # Store component info
                self._items[name] = RegistryItem(
                    name=name,
                    description=description or comp.__doc__,
                    version=version,
                    metadata=metadata or {}
                )
                
                # Update metrics
                self.registration_count += 1
                
                logger.info(
                    f"Registered {self._name} component '{name}' "
                    f"v{version}"
                )
                return comp
                
            except Exception as e:
                logger.error(f"Component registration failed: {str(e)}")
                raise RegistrationError(
                    message=f"Failed to register component '{name}': {str(e)}",
                    details={
                        "name": name,
                        "version": version,
                        "type": comp.__name__
                    }
                )
        
        if component is not None:
            return decorator(component)
            
        return decorator
    
    def get(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Optional[Type[T]]:
        """Get registered component
        
        Args:
            name: Component name
            version: Optional version requirement
            
        Returns:
            Optional component class
            
        Raises:
            KeyError: If component not found
        """
        if name not in self._registry:
            raise KeyError(
                f"Component '{name}' not found in {self._name} registry"
            )
            
        component = self._registry[name]
        
        if version and self._items[name].version != version:
            raise KeyError(
                f"Component '{name}' version {version} not found "
                f"(found {self._items[name].version})"
            )
            
        return component
    
    def build(
        self,
        name: str,
        **kwargs
    ) -> T:
        """Build component instance
        
        Args:
            name: Component name
            **kwargs: Component arguments
            
        Returns:
            Component instance
            
        Raises:
            KeyError: If component not found
        """
        component_class = self.get(name)
        return component_class(**kwargs)
    
    def list(
        self,
        include_metadata: bool = False
    ) -> List[str]:
        """List registered components
        
        Args:
            include_metadata: Whether to include metadata
            
        Returns:
            List of component names or info
        """
        if include_metadata:
            return [
                {
                    "name": name,
                    **item.model_dump()
                }
                for name, item in self._items.items()
            ]
        return list(self._registry.keys())
    
    def get_info(
        self,
        name: str
    ) -> Optional[RegistryItem]:
        """Get component information
        
        Args:
            name: Component name
            
        Returns:
            Optional component info
        """
        return self._items.get(name)
    
    def unregister(
        self,
        name: str
    ) -> None:
        """Unregister component
        
        Args:
            name: Component name
        """
        self._registry.pop(name, None)
        self._items.pop(name, None)
        logger.info(f"Unregistered {self._name} component '{name}'")
    
    def _validate_component(
        self,
        component: Type[T]
    ) -> None:
        """Validate component
        
        Args:
            component: Component to validate
            
        Raises:
            RegistrationError: If validation fails
        """
        # Override in subclasses
        pass
    
    def reset(self) -> None:
        """Reset registry state"""
        self._registry.clear()
        self._items.clear()
        self.registration_count = 0
        logger.info(f"Reset {self._name} registry")
    
    def __contains__(
        self,
        name: str
    ) -> bool:
        """Check if component is registered
        
        Args:
            name: Component name
            
        Returns:
            Whether component exists
        """
        return name in self._registry
    
    def __len__(self) -> int:
        """Get number of registered components
        
        Returns:
            Component count
        """
        return len(self._registry)
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"name='{self._name}', "
            f"components={len(self)})"
        ) 