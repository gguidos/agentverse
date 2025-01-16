"""
Selectors Module

This module provides selection and filtering mechanisms for AgentVerse:

1. Selection Types:
   - Agent Selectors: Choose appropriate agents
   - Memory Selectors: Filter relevant memories
   - Message Selectors: Filter messages
   - Task Selectors: Choose next tasks

2. Selection Features:
   - Priority-based selection
   - Relevance filtering
   - Pattern matching
   - Rule-based filtering

3. Selection Strategies:
   - Random Selection
   - Round Robin
   - Weighted Selection
   - Conditional Selection

Example Usage:
    ```python
    from src.core.agentverse.environment.selectors import (
        AgentSelector,
        MemorySelector,
        TaskSelector
    )

    # Select agents based on capabilities
    agent_selector = AgentSelector()
    selected_agents = await agent_selector.select(
        required_capabilities=["math", "coding"],
        count=2
    )

    # Filter relevant memories
    memory_selector = MemorySelector()
    relevant_memories = await memory_selector.select(
        query="python programming",
        min_relevance=0.7,
        max_results=5
    )

    # Choose next task
    task_selector = TaskSelector()
    next_task = await task_selector.select(
        available_tasks=task_list,
        priority="high",
        agent_id="agent_1"
    )
    ```

Selection Process:
    ```
    Selection
    ├── Input
    │   ├── Candidates
    │   ├── Criteria
    │   └── Constraints
    ├── Processing
    │   ├── Filtering
    │   ├── Scoring
    │   └── Ranking
    └── Output
        ├── Selected Items
        ├── Scores
        └── Metadata
    ```
"""

from src.core.agentverse.environment.selectors.base import BaseSelector
from src.core.agentverse.environment.selectors.agent import AgentSelector
from src.core.agentverse.environment.selectors.memory import MemorySelector
from src.core.agentverse.environment.selectors.task import TaskSelector
from src.core.agentverse.environment.selectors.message import MessageSelector

__all__ = [
    # Base
    'BaseSelector',
    
    # Selector Types
    'AgentSelector',
    'MemorySelector',
    'TaskSelector',
    'MessageSelector'
]

# Version
__version__ = "1.0.0" 