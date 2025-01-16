"""
Updaters Module

This module provides state and configuration update mechanisms for AgentVerse:

1. Update Types:
   - State Updates: Runtime state changes
   - Config Updates: Configuration modifications
   - Model Updates: Model parameter updates
   - Resource Updates: Resource allocation changes

2. Update Features:
   - Atomic updates
   - Batch updates
   - Validation
   - Rollback support

3. Update Strategies:
   - Immediate Updates
   - Deferred Updates
   - Conditional Updates
   - Scheduled Updates

Example Usage:
    ```python
    from src.core.agentverse.environment.updaters import (
        StateUpdater,
        ConfigUpdater,
        ModelUpdater
    )

    # Update agent state
    state_updater = StateUpdater()
    await state_updater.update(
        agent_id="agent_1",
        updates={
            "status": "busy",
            "memory.usage": 85.5,
            "tasks.active": 3
        }
    )

    # Update configuration
    config_updater = ConfigUpdater()
    await config_updater.update(
        component="memory",
        updates={
            "max_size": 10000,
            "ttl": 3600,
            "backend": "redis"
        }
    )

    # Update model parameters
    model_updater = ModelUpdater()
    await model_updater.update(
        model_id="gpt-4",
        updates={
            "temperature": 0.7,
            "max_tokens": 2000,
            "presence_penalty": 0.5
        }
    )
    ```

Update Process:
    ```
    Update
    ├── Validation
    │   ├── Schema Check
    │   ├── Type Check
    │   └── Constraint Check
    ├── Execution
    │   ├── Backup
    │   ├── Apply
    │   └── Verify
    └── Completion
        ├── Notify
        ├── Log
        └── Cleanup
    ```
"""

from src.core.agentverse.environment.updaters.base import (
    BaseUpdater,
    UpdateResult
)
from src.core.agentverse.environment.updaters.state import StateUpdater
from src.core.agentverse.environment.updaters.config import ConfigUpdater
from src.core.agentverse.environment.updaters.model import ModelUpdater
from src.core.agentverse.environment.updaters.resource import ResourceUpdater

__all__ = [
    # Base
    'BaseUpdater',
    'UpdateResult',
    
    # Updater Types
    'StateUpdater',
    'ConfigUpdater',
    'ModelUpdater',
    'ResourceUpdater'
]

# Version
__version__ = "1.0.0" 