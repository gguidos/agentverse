from typing import Dict, Any, Optional, Type, List, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.exceptions import RegistrationError, ComponentNotFoundError

logger = logging.getLogger(__name__)

class RegistryEntry(BaseModel):
    """Registry entry for agent type"""
    name: str
    agent_class: Type[BaseAgent]
    description: Optional[str] = None
    version: str = "1.0.0"
    capabilities: List[str] = Field(default_factory=list)
    registration_time: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class AgentRegistry(BaseModel):
    """Registry for managing agent types"""
    
    name: ClassVar[str] = "agent_registry"
    description: ClassVar[str] = "Registry for agent types"
    version: ClassVar[str] = "1.1.0"
    
    entries: Dict[str, RegistryEntry] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
    
    def register(
        self,
        name: str,
        description: Optional[str] = None,
        version: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register agent class
        
        Args:
            name: Agent type name
            description: Optional description
            version: Optional version
            capabilities: Optional capabilities
            metadata: Optional metadata
            
        Returns:
            Registration decorator
            
        Raises:
            RegistrationError: If registration fails
        """
        def decorator(agent_class: Type[BaseAgent]) -> Type[BaseAgent]:
            try:
                # Validate agent class
                if not issubclass(agent_class, BaseAgent):
                    raise RegistrationError(
                        message=f"Class {agent_class.__name__} must inherit from BaseAgent",
                        details={"class": agent_class.__name__}
                    )
                
                # Create registry entry
                entry = RegistryEntry(
                    name=name,
                    agent_class=agent_class,
                    description=description or agent_class.__doc__,
                    version=version or getattr(agent_class, "version", "1.0.0"),
                    capabilities=capabilities or getattr(agent_class, "capabilities", []),
                    metadata=metadata or {}
                )
                
                # Store entry
                self.entries[name] = entry
                logger.info(f"Registered agent type '{name}' v{entry.version}")
                
                return agent_class
                
            except Exception as e:
                logger.error(f"Agent registration failed: {str(e)}")
                raise RegistrationError(
                    message=f"Failed to register agent type: {str(e)}",
                    details={
                        "name": name,
                        "class": agent_class.__name__
                    }
                )
        
        return decorator
    
    def build(
        self,
        agent_type: str,
        **kwargs
    ) -> BaseAgent:
        """Build agent instance
        
        Args:
            agent_type: Agent type name
            **kwargs: Agent constructor arguments
            
        Returns:
            Agent instance
            
        Raises:
            ComponentNotFoundError: If agent type not found
            RegistrationError: If build fails
        """
        try:
            # Get registry entry
            entry = self.entries.get(agent_type)
            if not entry:
                raise ComponentNotFoundError(
                    message=f"Agent type '{agent_type}' not found",
                    details={
                        "available": list(self.entries.keys())
                    }
                )
            
            # Create instance
            agent = entry.agent_class(**kwargs)
            logger.info(
                f"Built agent '{agent_type}' "
                f"v{entry.version}"
            )
            
            return agent
            
        except ComponentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Agent build failed: {str(e)}")
            raise RegistrationError(
                message=f"Failed to build agent: {str(e)}",
                details={
                    "type": agent_type,
                    "args": kwargs
                }
            )
    
    def get_entry(
        self,
        name: str
    ) -> Optional[RegistryEntry]:
        """Get registry entry
        
        Args:
            name: Entry name
            
        Returns:
            Optional registry entry
        """
        return self.entries.get(name)
    
    def list_entries(
        self,
        capability: Optional[str] = None
    ) -> List[RegistryEntry]:
        """List registry entries
        
        Args:
            capability: Optional capability filter
            
        Returns:
            List of entries
        """
        entries = list(self.entries.values())
        
        if capability:
            entries = [
                entry for entry in entries
                if capability in entry.capabilities
            ]
            
        return sorted(
            entries,
            key=lambda e: (e.name, e.version)
        )
    
    def get_capabilities(self) -> Dict[str, List[str]]:
        """Get capability mapping
        
        Returns:
            Mapping of capabilities to agent types
        """
        capabilities = {}
        for entry in self.entries.values():
            for cap in entry.capabilities:
                capabilities.setdefault(cap, []).append(entry.name)
        return capabilities
    
    def unregister(
        self,
        name: str
    ) -> None:
        """Unregister agent type
        
        Args:
            name: Agent type name
        """
        self.entries.pop(name, None)
        logger.info(f"Unregistered agent type '{name}'")
    
    def reset(self) -> None:
        """Reset registry state"""
        self.entries.clear()
        self.metadata.clear()
        logger.info(f"Reset {self.name}")

# Create global instance
agent_registry = AgentRegistry()

# Export instance
__all__ = ['agent_registry'] 