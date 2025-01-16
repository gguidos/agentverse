"""
AgentVerse Registry Module

This module provides a registry system for managing and accessing different components
in the AgentVerse ecosystem. It includes base registry functionality, specialized registries
for different component types, and a centralized registry management system.

Key Components:
    - Base Registry: Generic registry implementation for component management
    - Agent Registry: Specialized registry for agent components
    - Component Registries: Pre-configured registries for memories, LLMs, parsers, etc.
    - Registry Management: Utilities for accessing and managing registries

Available Registries:
    - agent_registry: Registry for agent components
    - memory_registry: Registry for memory components
    - llm_registry: Registry for LLM components
    - parser_registry: Registry for parser components
    - environment_registry: Registry for environment components

Example Usage:
    >>> from src.core.agentverse.registry import agent_registry, Registry
    >>> 
    >>> # Register a component
    >>> @agent_registry.register("my_agent")
    >>> class MyAgent(BaseAgent):
    ...     pass
    >>> 
    >>> # Get a registry
    >>> from src.core.agentverse.registry import get_registry
    >>> parser_reg = get_registry("parser")
"""

from src.core.agentverse.registry.base import (
    Registry,
    RegistryItem
)

from src.core.agentverse.registry.agent_registry import (
    AgentRegistry,
    RegistryEntry
)

from src.core.agentverse.registry.registries import (
    agent_registry,
    memory_registry,
    llm_registry,
    parser_registry,
    environment_registry,
    registries,
    get_registry,
    reset_registries
)

__all__ = [
    # Base classes
    "Registry",
    "RegistryItem",
    
    # Agent registry
    "AgentRegistry",
    "RegistryEntry",
    
    # Registry instances
    "agent_registry",
    "memory_registry",
    "llm_registry",
    "parser_registry",
    "environment_registry",
    
    # Registry management
    "registries",
    "get_registry",
    "reset_registries"
] 