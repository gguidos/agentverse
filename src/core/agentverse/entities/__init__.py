"""
Entities Module

This module manages different types of entities within the AgentVerse environment:

1. Entity Types:
   - Agents: Autonomous actors
   - Resources: Shared resources
   - Tasks: Work units
   - Messages: Communication units
   - States: Entity states

2. Entity Features:
   - Lifecycle management
   - State tracking
   - Relationship mapping
   - Capability management
   - Access control

3. Entity Operations:
   - Creation/Deletion
   - State updates
   - Relationship updates
   - Capability checks
   - Permission checks

Example Usage:
    ```python
    from src.core.agentverse.entities import (
        Agent,
        Resource,
        Task,
        EntityRegistry
    )

    # Create agent
    agent = Agent(
        id="agent_1",
        name="Helper",
        capabilities=["math", "coding"],
        state={
            "status": "idle",
            "memory_usage": 0,
            "task_count": 0
        }
    )

    # Create resource
    resource = Resource(
        id="memory_1",
        type="vector_store",
        capacity=1000,
        access_policy={
            "read": ["agent_1", "agent_2"],
            "write": ["agent_1"]
        }
    )

    # Create task
    task = Task(
        id="task_1",
        type="computation",
        requirements=["math"],
        assigned_to="agent_1",
        priority="high"
    )

    # Register entities
    registry = EntityRegistry()
    registry.register_agent(agent)
    registry.register_resource(resource)
    registry.register_task(task)
    ```

Entity Structure:
    ```
    Entity
    ├── Identity
    │   ├── ID
    │   ├── Type
    │   └── Metadata
    ├── State
    │   ├── Status
    │   ├── Attributes
    │   └── History
    ├── Relationships
    │   ├── Dependencies
    │   ├── Permissions
    │   └── Groups
    └── Operations
        ├── Actions
        ├── Updates
        └── Checks
    ```
"""

from src.core.agentverse.entities.base import (
    BaseEntity,
    EntityConfig,
    EntityState
)
from src.core.agentverse.entities.agent import Agent
from src.core.agentverse.entities.resource import Resource
from src.core.agentverse.entities.task import Task
from src.core.agentverse.entities.message import Message
from src.core.agentverse.entities.registry import EntityRegistry

__all__ = [
    # Base
    'BaseEntity',
    'EntityConfig',
    'EntityState',
    
    # Entity Types
    'Agent',
    'Resource',
    'Task',
    'Message',
    
    # Registry
    'EntityRegistry'
]

# Version
__version__ = "1.0.0"