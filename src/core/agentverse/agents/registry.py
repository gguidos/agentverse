"""
Agent registry module
"""

from typing import Dict, Type, Any, Callable
from src.core.agentverse.agents.base import BaseAgent

class AgentRegistry:
    """Registry for agent types"""
    
    def __init__(self):
        self._registry: Dict[str, Type[BaseAgent]] = {}
    
    def register(self, agent_type: str) -> Callable:
        """Register agent class decorator
        
        Args:
            agent_type: Type identifier for agent
            
        Returns:
            Registration decorator
        """
        def decorator(cls: Type[BaseAgent]) -> Type[BaseAgent]:
            self._registry[agent_type] = cls
            return cls
        return decorator
    
    def get(self, agent_type: str) -> Type[BaseAgent]:
        """Get agent class by type
        
        Args:
            agent_type: Agent type identifier
            
        Returns:
            Agent class
            
        Raises:
            KeyError: If agent type not found
        """
        if agent_type not in self._registry:
            raise KeyError(f"Agent type not found: {agent_type}")
        return self._registry[agent_type]

# Global registry instance
agent_registry = AgentRegistry() 