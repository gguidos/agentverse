from typing import Dict, Type, Any, List
from src.core.agentverse.agents.base_agent import BaseAgent
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RegistryEntry:
    """A registry entry that stores the class and its metadata."""
    cls: Type[Any]
    name: str
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class AgentRegistry:
    """Registry for agent types"""
    
    def __init__(self):
        self._registry: Dict[str, Type[BaseAgent]] = {}
        
    def register(self, agent_type: str):
        """Register an agent class"""
        def decorator(agent_class: Type[BaseAgent]):
            logger.info(f"Registering agent type: {agent_type}")
            self._registry[agent_type] = agent_class
            logger.debug(f"Current registry state: {self.get_registration_info()}")
            return agent_class
        return decorator
        
    def get(self, agent_type: str) -> Type[BaseAgent]:
        """Get agent class by type"""
        if agent_type not in self._registry:
            raise KeyError(f"Agent type '{agent_type}' not found")
        return self._registry[agent_type]
        
    def get_registered_types(self) -> List[str]:
        """Get all registered agent types"""
        return list(self._registry.keys())
        
    def get_registry(self) -> Dict[str, Type[BaseAgent]]:
        """Get full registry"""
        return self._registry
        
    def reset(self) -> None:
        """Clear registry"""
        self._registry.clear()
        logger.info("Agent registry reset") 
        
    def is_registered(self, agent_type: str) -> bool:
        """Check if agent type is registered"""
        return agent_type in self._registry
        
    def get_registration_info(self) -> Dict[str, Any]:
        """Get registration status info"""
        return {
            "registered_types": list(self._registry.keys()),
            "count": len(self._registry),
            "registry_status": "active" if self._registry else "empty"
        } 