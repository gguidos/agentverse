"""
AgentVerse Framework

AgentVerse is a framework for building and orchestrating multi-agent systems.
It provides a comprehensive set of tools and abstractions for creating,
managing, and coordinating AI agents in various environments.

Key Components:
    - Agents: Different types of AI agents and their behaviors
    - Environment: Shared spaces where agents interact
    - Tools: Utilities and capabilities available to agents
    - Tasks: Structured work units for agents to complete
    - Services: External service integrations (LLM, Embedding, etc.)
    - Entities: Core domain objects and their relationships

Example Usage:
    >>> from src.core.agentverse import AgentVerse
    >>> from src.core.agentverse.tasks import load_task
    >>> 
    >>> # Load task configuration
    >>> task_config = load_task("chat_task.yaml")
    >>> 
    >>> # Create AgentVerse instance
    >>> agentverse = AgentVerse(
    ...     agents=task_config.agents,
    ...     environment=task_config.environment
    ... )
    >>> 
    >>> # Execute the task
    >>> results = await agentverse.run()

Module Structure:
    agentverse/
    ├── agents/          # Agent implementations
    ├── environment/     # Environment definitions
    ├── tools/          # Agent tools and utilities
    ├── services/       # External service integrations
    ├── tasks/          # Task definitions and handlers
    ├── entities/       # Core domain entities
    └── orchestration/  # Task orchestration
"""

from src.core.agentverse.agentverse import (
    AgentVerse,
    AgentVerseConfig
)

from src.core.agentverse.exceptions import AgentVerseError

# Import main components
from src.core.agentverse import (
    agents,
    environment,
    tools,
    services,
    tasks,
    entities,
    orchestration
)

__all__ = [
    # Main classes
    "AgentVerse",
    "AgentVerseConfig",
    "AgentVerseError",
    
    # Major components
    "agents",
    "environment",
    "tools", 
    "services",
    "tasks",
    "entities",
    "orchestration"
]

# Version info
__version__ = "1.1.0"
__author__ = "AgentVerse Team"
__license__ = "MIT" 