"""
Models Module

This module defines the core data models and structures used throughout AgentVerse:

1. Chat Models:
   - Message Models: Chat message structures
   - Conversation Models: Conversation tracking
   - Role Models: Agent role definitions
   - Function Models: Function calling schemas

2. Agent Models:
   - Agent Profiles: Agent configuration and state
   - Agent Capabilities: Available agent actions
   - Agent Relationships: Inter-agent connections
   - Agent Metrics: Performance tracking

3. System Models:
   - Configuration Models: System settings
   - Environment Models: Runtime environment
   - Resource Models: Resource management
   - Metrics Models: System monitoring

Example Usage:
    ```python
    from src.core.agentverse.models import (
        ChatMessage,
        AgentProfile,
        SystemConfig
    )

    # Create a chat message model
    message = ChatMessage(
        role="assistant",
        content="Hello!",
        name="helper_agent",
        function_call=None
    )

    # Create an agent profile
    agent = AgentProfile(
        name="helper_agent",
        description="Helpful assistant",
        capabilities=["chat", "math", "coding"],
        configuration={
            "temperature": 0.7,
            "max_tokens": 1000
        }
    )

    # Create system configuration
    config = SystemConfig(
        environment="production",
        log_level="INFO",
        max_agents=10,
        timeout=30
    )
    ```

Model Relationships:
    ```
    BaseModel
    ├── ChatModels
    │   ├── Message
    │   ├── Conversation
    │   └── Function
    ├── AgentModels
    │   ├── Profile
    │   ├── Capability
    │   └── Metric
    └── SystemModels
        ├── Config
        ├── Environment
        └── Resource
    ```
"""

from src.core.agentverse.models.chat import (
    ChatMessage,
    Conversation,
    Function,
    FunctionCall
)

from src.core.agentverse.models.agent import (
    AgentProfile,
    AgentCapability,
    AgentMetric
)

from src.core.agentverse.models.system import (
    SystemConfig,
    Environment,
    Resource
)

__all__ = [
    # Chat Models
    'ChatMessage',
    'Conversation',
    'Function',
    'FunctionCall',
    
    # Agent Models
    'AgentProfile',
    'AgentCapability',
    'AgentMetric',
    
    # System Models
    'SystemConfig',
    'Environment',
    'Resource'
]

# Version
__version__ = "1.0.0" 