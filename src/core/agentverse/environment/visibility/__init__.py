"""
Visibility Module

This module manages visibility and access control between agents in AgentVerse:

1. Visibility Types:
   - All: Visible to all agents
   - Base: Default visibility rules
   - Group: Group-based visibility
   - Self: Self-only visibility
   - Simple: Basic visibility rules
   - Evaluation: Conditional visibility

2. Visibility Features:
   - Access control
   - Permission management
   - Visibility rules
   - Information filtering

3. Visibility Scopes:
   - Message visibility
   - Memory visibility
   - State visibility
   - Resource visibility

Example Usage:
    ```python
    from src.core.agentverse.environment.visibility import (
        AllVisibility,
        GroupVisibility,
        SelfVisibility
    )

    # All agents visibility
    visibility = AllVisibility()
    can_access = await visibility.check_access(
        agent_id="agent_1",
        target_id="agent_2",
        resource_type="message"
    )

    # Group-based visibility
    group_visibility = GroupVisibility(
        groups={
            "team_a": ["agent_1", "agent_2"],
            "team_b": ["agent_3", "agent_4"]
        }
    )
    visible_agents = await group_visibility.get_visible_agents(
        agent_id="agent_1"
    )

    # Self-only visibility
    self_visibility = SelfVisibility()
    can_see = await self_visibility.is_visible(
        source="agent_1",
        target="memory_1"
    )
    ```

Visibility Rules:
    ```
    Visibility
    ├── Scope
    │   ├── Agent
    │   ├── Resource
    │   └── Operation
    ├── Rules
    │   ├── Allow
    │   ├── Deny
    │   └── Conditions
    └── Enforcement
        ├── Check
        ├── Filter
        └── Audit
    ```
"""

from src.core.agentverse.environment.visibility.base import (
    BaseVisibility,
    VisibilityConfig
)
from src.core.agentverse.environment.visibility.audit import VisibilityAudit
from src.core.agentverse.environment.visibility.storage import (
    AuditStorage,
    MongoAuditStorage
)
from src.core.agentverse.environment.visibility.all import AllVisibility
from src.core.agentverse.environment.visibility.group import GroupVisibility
from src.core.agentverse.environment.visibility.self_only import SelfVisibility
from src.core.agentverse.environment.visibility.simple import SimpleVisibility
from src.core.agentverse.environment.visibility.evaluation import EvaluationVisibility

__all__ = [
    # Base
    'BaseVisibility',
    'VisibilityConfig',
    'VisibilityAudit',
    'AuditStorage',
    'MongoAuditStorage',
    
    # Visibility Types
    'AllVisibility',
    'GroupVisibility',
    'SelfVisibility',
    'SimpleVisibility',
    'EvaluationVisibility'
]

# Version
__version__ = "1.0.0" 