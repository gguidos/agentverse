"""
AgentVerse Agents Module

This module provides different types of agents and agent-related functionality.
"""

from typing import Dict, Type

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.agents.config import (
    AgentConfig,
    AssistantAgentConfig,
    UserAgentConfig,
    FunctionAgentConfig
)
from src.core.agentverse.agents.assistant import AssistantAgent
from src.core.agentverse.agents.user import UserAgent
from src.core.agentverse.agents.function import FunctionAgent

# Registry of available agent types
AGENT_TYPES: Dict[str, Type[BaseAgent]] = {
    "assistant": AssistantAgent,
    "user": UserAgent,
    "function": FunctionAgent
}

def create_agent(
    agent_type: str,
    config: AgentConfig,
    **kwargs
) -> BaseAgent:
    """Create agent instance
    
    Args:
        agent_type: Type of agent to create
        config: Agent configuration
        **kwargs: Additional agent arguments
        
    Returns:
        Created agent instance
        
    Raises:
        ValueError: If agent type not found
    """
    if agent_type not in AGENT_TYPES:
        raise ValueError(f"Unknown agent type: {agent_type}")
        
    agent_class = AGENT_TYPES[agent_type]
    return agent_class(config=config, **kwargs)

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentConfig",
    
    # Agent types
    "AssistantAgent",
    "UserAgent",
    "FunctionAgent",
    
    # Configs
    "AssistantAgentConfig",
    "UserAgentConfig", 
    "FunctionAgentConfig",
    
    # Factory
    "create_agent",
    "AGENT_TYPES"
] 