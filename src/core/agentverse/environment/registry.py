from typing import Dict, Type, Optional, List, Any, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

class EnvironmentInfo(BaseModel):
    """Information about registered environment"""
    name: str
    description: str
    version: str
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    usage_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EnvironmentRegistry(BaseModel):
    """Registry for environment types"""
    
    name: ClassVar[str] = "environment_registry"
    description: ClassVar[str] = "Registry for environment implementations"
    version: ClassVar[str] = "1.1.0"
    
    entries: Dict[str, Type[BaseEnvironment]] = Field(default_factory=dict)
    info: Dict[str, EnvironmentInfo] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
    
    def register(self, key: str, **metadata):
        """Register an environment class
        
        Args:
            key: Registry key for environment
            **metadata: Additional metadata for environment
            
        Returns:
            Decorator function
            
        Raises:
            ConfigurationError: If registration fails
        """
        def decorator(env_class: Type[BaseEnvironment]):
            try:
                # Validate environment class
                if not issubclass(env_class, BaseEnvironment):
                    raise ValueError(
                        f"Class {env_class.__name__} must inherit from BaseEnvironment"
                    )
                
                # Check for existing registration
                if key in self.entries:
                    raise ValueError(f"Environment '{key}' already registered")
                
                # Register environment
                self.entries[key] = env_class
                
                # Store environment info
                self.info[key] = EnvironmentInfo(
                    name=getattr(env_class, 'name', key),
                    description=getattr(env_class, 'description', ''),
                    version=getattr(env_class, 'version', '1.0.0'),
                    metadata=metadata
                )
                
                logger.info(f"Registered environment '{key}' ({env_class.__name__})")
                return env_class
                
            except Exception as e:
                raise ConfigurationError(
                    message=f"Failed to register environment: {str(e)}",
                    config_key=key,
                    details={"class": env_class.__name__}
                )
                
        return decorator
    
    def build(
        self,
        type: str,
        **kwargs
    ) -> BaseEnvironment:
        """Build an environment instance
        
        Args:
            type: Environment type to build
            **kwargs: Arguments for environment initialization
            
        Returns:
            BaseEnvironment: Initialized environment
            
        Raises:
            ConfigurationError: If build fails
        """
        try:
            if type not in self.entries:
                available = list(self.entries.keys())
                raise ValueError(
                    f'Environment type "{type}" not found. '
                    f'Available types: {available}'
                )
            
            # Update usage count
            self.info[type].usage_count += 1
            
            # Initialize environment
            env = self.entries[type](**kwargs)
            logger.info(f"Built environment '{type}' (id: {env.id})")
            return env
            
        except Exception as e:
            raise ConfigurationError(
                message=f"Failed to build environment: {str(e)}",
                config_key=type,
                config_value=kwargs
            )
    
    def get(self, key: str) -> Type[BaseEnvironment]:
        """Get a registered environment class
        
        Args:
            key: Environment key to get
            
        Returns:
            Type[BaseEnvironment]: Environment class
            
        Raises:
            ConfigurationError: If environment not found
        """
        if key not in self.entries:
            raise ConfigurationError(
                message=f"Environment '{key}' not found",
                config_key=key,
                details={"available": list(self.entries.keys())}
            )
        return self.entries[key]
    
    def list_environments(self) -> Dict[str, Dict[str, Any]]:
        """List all registered environments with info"""
        return {
            key: {
                "name": info.name,
                "description": info.description,
                "version": info.version,
                "registered_at": info.registered_at.isoformat(),
                "usage_count": info.usage_count,
                "metadata": info.metadata
            }
            for key, info in self.info.items()
        }
    
    def get_most_used(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most frequently used environments"""
        sorted_envs = sorted(
            self.info.items(),
            key=lambda x: x[1].usage_count,
            reverse=True
        )
        
        return [{
            "key": key,
            "name": info.name,
            "usage_count": info.usage_count,
            "version": info.version
        } for key, info in sorted_envs[:limit]]
    
    def unregister(self, key: str) -> None:
        """Unregister an environment
        
        Args:
            key: Environment key to unregister
        """
        if key in self.entries:
            del self.entries[key]
            del self.info[key]
            logger.info(f"Unregistered environment '{key}'")
    
    def clear(self) -> None:
        """Clear all registered environments"""
        self.entries.clear()
        self.info.clear()
        logger.info("Cleared environment registry")

class OrderRegistry(BaseModel):
    """Registry for environment orders/commands"""
    
    name: ClassVar[str] = "order_registry"
    description: ClassVar[str] = "Registry for environment orders and commands"
    version: ClassVar[str] = "1.1.0"
    
    entries: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
    
    def register(self, key: str, **metadata):
        """Register an order class
        
        Args:
            key: Registry key for order
            **metadata: Additional metadata for order
        """
        def decorator(order_class):
            self.entries[key] = order_class
            self.metadata[key] = {
                "registered_at": datetime.utcnow(),
                "usage_count": 0,
                **metadata
            }
            logger.info(f"Registered order '{key}'")
            return order_class
        return decorator
    
    def get(self, key: str) -> Any:
        """Get a registered order
        
        Args:
            key: Order key to get
            
        Returns:
            Registered order class
            
        Raises:
            ConfigurationError: If order not found
        """
        if key not in self.entries:
            raise ConfigurationError(
                message=f"Order '{key}' not found",
                config_key=key,
                details={"available": self.list_orders()}
            )
            
        # Update usage count
        self.metadata[key]["usage_count"] += 1
        return self.entries[key]
    
    def list_orders(self) -> List[str]:
        """List all registered orders"""
        return list(self.entries.keys())
    
    def get_metadata(self, key: str) -> Dict[str, Any]:
        """Get metadata for an order"""
        if key not in self.metadata:
            raise ConfigurationError(
                message=f"Order '{key}' not found",
                config_key=key
            )
        return self.metadata[key]

# Create global registry instances
env_registry = EnvironmentRegistry()
order_registry = OrderRegistry()

__all__ = ['env_registry', 'order_registry'] 