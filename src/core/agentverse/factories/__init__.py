"""
Factories Module

This module provides factory classes for creating AgentVerse components:

1. Factory Types:
   - Agent Factory: Creates agent instances
   - Environment Factory: Creates environments
   - Task Factory: Creates tasks
   - Message Factory: Creates messages
   - Resource Factory: Creates resources

2. Factory Features:
   - Object instantiation
   - Configuration management
   - Dependency injection
   - Validation
   - Default settings

3. Factory Operations:
   - Create objects
   - Configure instances
   - Register builders
   - Validate configurations
   - Apply defaults

Example Usage:
    ```python
    from src.core.agentverse.factories import (
        AgentFactory,
        EnvironmentFactory,
        TaskFactory
    )

    # Create agent
    agent = await AgentFactory.create(
        agent_type="helper",
        config={
            "name": "math_helper",
            "capabilities": ["math", "logic"],
            "memory_size": 1000
        }
    )

    # Create environment
    env = await EnvironmentFactory.create(
        env_type="development",
        config={
            "max_agents": 10,
            "visibility": "group",
            "logging": True
        }
    )

    # Create task
    task = await TaskFactory.create(
        task_type="computation",
        config={
            "priority": "high",
            "requirements": ["math"],
            "deadline": "2h"
        }
    )
    ```

Factory Structure:
    ```
    Factory
    ├── Configuration
    │   ├── Templates
    │   ├── Defaults
    │   └── Validators
    ├── Builders
    │   ├── Components
    │   ├── Assemblers
    │   └── Decorators
    ├── Registry
    │   ├── Types
    │   ├── Builders
    │   └── Configs
    └── Validation
        ├── Rules
        ├── Schemas
        └── Errors
    ```
"""

from src.core.agentverse.factories.base import BaseFactory
from src.core.agentverse.factories.agent import AgentFactory
from src.core.agentverse.factories.environment import EnvironmentFactory
from src.core.agentverse.factories.task import TaskFactory
from src.core.agentverse.factories.message import MessageFactory
from src.core.agentverse.factories.resource import ResourceFactory
from src.core.agentverse.factories.registry import FactoryRegistry

# Memory & Storage
from src.core.agentverse.factories.memory import MemoryFactory
from src.core.agentverse.factories.storage import StorageFactory
from src.core.agentverse.factories.cache import CacheFactory

# Communication
from src.core.agentverse.factories.protocol import ProtocolFactory
from src.core.agentverse.factories.channel import ChannelFactory
from src.core.agentverse.factories.transport import TransportFactory

# Policies & Rules
from src.core.agentverse.factories.policy import PolicyFactory
from src.core.agentverse.factories.rule import RuleFactory
from src.core.agentverse.factories.validator import ValidatorFactory

# Behaviors
from src.core.agentverse.factories.strategy import StrategyFactory
from src.core.agentverse.factories.behavior import BehaviorFactory
from src.core.agentverse.factories.personality import PersonalityFactory

# Integrations
from src.core.agentverse.factories.connector import ConnectorFactory
from src.core.agentverse.factories.adapter import AdapterFactory
from src.core.agentverse.factories.provider import ProviderFactory

__all__ = [
    # Base
    'BaseFactory',
    
    # Core Types
    'AgentFactory',
    'EnvironmentFactory',
    'TaskFactory',
    'MessageFactory',
    'ResourceFactory',
    
    # Memory & Storage
    'MemoryFactory',
    'StorageFactory',
    'CacheFactory',
    
    # Communication
    'ProtocolFactory',
    'ChannelFactory',
    'TransportFactory',
    
    # Policies & Rules
    'PolicyFactory',
    'RuleFactory',
    'ValidatorFactory',
    
    # Behaviors
    'StrategyFactory',
    'BehaviorFactory',
    'PersonalityFactory',
    
    # Integrations
    'ConnectorFactory',
    'AdapterFactory',
    'ProviderFactory',
    
    # Registry
    'FactoryRegistry'
]

# Version
__version__ = "1.0.0"