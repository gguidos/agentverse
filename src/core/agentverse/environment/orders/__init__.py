"""
Orders Module

This module manages task ordering and execution flow in AgentVerse:

1. Order Types:
   - Sequential Orders: Step-by-step execution
   - Parallel Orders: Concurrent execution
   - Conditional Orders: Branching execution
   - Priority Orders: Importance-based execution

2. Order Features:
   - Task Scheduling
   - Dependency Management
   - Priority Handling
   - Error Recovery

3. Order States:
   - Pending: Not yet started
   - Running: Currently executing
   - Completed: Successfully finished
   - Failed: Error occurred
   - Cancelled: Manually stopped

Example Usage:
    ```python
    from src.core.agentverse.orders import (
        OrderManager,
        SequentialOrder,
        ParallelOrder
    )

    # Create a sequential order
    order = SequentialOrder(
        name="process_data",
        steps=[
            {"action": "load_data", "args": {"file": "data.csv"}},
            {"action": "clean_data", "args": {"remove_nulls": True}},
            {"action": "save_results", "args": {"output": "results.json"}}
        ]
    )

    # Create a parallel order
    parallel_order = ParallelOrder(
        name="analyze_data",
        tasks=[
            {"action": "calculate_stats", "args": {"metrics": ["mean", "std"]}},
            {"action": "generate_plots", "args": {"type": "histogram"}},
            {"action": "run_validation", "args": {"rules": ["range", "null"]}}
        ],
        max_workers=3
    )

    # Execute orders
    async with OrderManager() as manager:
        # Run sequential order
        result = await manager.execute(order)
        
        # Run parallel order
        results = await manager.execute(parallel_order)
    ```

Order Structure:
    ```
    Order
    ├── Metadata
    │   ├── ID
    │   ├── Name
    │   ├── Priority
    │   └── Dependencies
    ├── Tasks
    │   ├── Actions
    │   ├── Arguments
    │   └── Handlers
    ├── State
    │   ├── Status
    │   ├── Progress
    │   └── Results
    └── Control
        ├── Start/Stop
        ├── Pause/Resume
        └── Cancel
    ```
"""

from src.core.agentverse.environment.orders.base import (
    BaseOrder,
    OrderStatus,
    OrderResult
)
from src.core.agentverse.environment.orders.sequential import SequentialOrder
from src.core.agentverse.environment.orders.parallel import ParallelOrder
from src.core.agentverse.environment.orders.conditional import ConditionalOrder
from src.core.agentverse.environment.orders.random import RandomOrder
from src.core.agentverse.environment.orders.manager import OrderManager

__all__ = [
    # Base
    'BaseOrder',
    'OrderStatus',
    'OrderResult',
    
    # Order Types
    'SequentialOrder',
    'ParallelOrder',
    'ConditionalOrder',
    'RandomOrder',
    
    # Management
    'OrderManager'
]

# Version
__version__ = "1.0.0"