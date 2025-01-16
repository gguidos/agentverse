from typing import Dict, Type
import logging

from src.core.agentverse.registry.base import Registry
from src.core.agentverse.registry.agent_registry import AgentRegistry
from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.memory.base import BaseMemory
from src.core.agentverse.llm.base import BaseLLM
from src.core.agentverse.parser.base import BaseParser
from src.core.agentverse.environment.base import BaseEnvironment

logger = logging.getLogger(__name__)

# Agent registry
agent_registry = AgentRegistry(
    name="agent",
    validate_components=True
)

# Memory registry
memory_registry = Registry[BaseMemory](
    name="memory",
    validate_components=True
)

# LLM registry
llm_registry = Registry[BaseLLM](
    name="llm",
    validate_components=True
)

# Parser registry
parser_registry = Registry[BaseParser](
    name="parser",
    validate_components=True
)

# Environment registry
environment_registry = Registry[BaseEnvironment](
    name="environment",
    validate_components=True
)

# Registry collection for easy access
registries: Dict[str, Registry] = {
    "agent": agent_registry,
    "memory": memory_registry,
    "llm": llm_registry,
    "parser": parser_registry,
    "environment": environment_registry
}

def get_registry(name: str) -> Registry:
    """Get registry by name
    
    Args:
        name: Registry name
        
    Returns:
        Registry instance
        
    Raises:
        KeyError: If registry not found
    """
    if name not in registries:
        raise KeyError(f"Registry '{name}' not found")
    return registries[name]

def reset_registries() -> None:
    """Reset all registries"""
    for registry in registries.values():
        registry.reset()
    logger.info("Reset all registries")

# Export registries
__all__ = [
    'agent_registry',
    'memory_registry', 
    'llm_registry',
    'parser_registry',
    'environment_registry',
    'registries',
    'get_registry',
    'reset_registries'
] 