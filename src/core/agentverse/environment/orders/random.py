"""Random Order Module"""

from typing import Dict, Any, Optional, List
from pydantic import Field, ConfigDict
from datetime import datetime
import random
import logging

from src.core.agentverse.environment.orders.base import (
    BaseOrder,
    OrderConfig,
    OrderResult,
    OrderStatus
)
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.exceptions import ActionError
from src.core.agentverse.environment.decorators import order

logger = logging.getLogger(__name__)

class RandomOrderConfig(OrderConfig):
    """Configuration for random order"""
    seed: Optional[int] = None
    batch_size: int = 1
    shuffle_batches: bool = True
    track_order: bool = True
    
    model_config = ConfigDict(
        extra="allow"
    )

@order
class RandomOrder(BaseOrder):
    """Random execution order"""
    
    name = "random_order"
    description = "Executes tasks in random order"
    version = "1.0.0"
    
    def __init__(self, config: Optional[RandomOrderConfig] = None):
        super().__init__(config or RandomOrderConfig())
        self.rng = random.Random(self.config.seed)
        self.execution_order = []
    
    async def execute(self, tasks: List[Dict[str, Any]]) -> OrderResult:
        """Execute tasks in random order"""
        # Create list of indices
        indices = list(range(len(tasks)))
        
        # Keep shuffling until order is different
        shuffled = indices.copy()
        while shuffled == indices:
            random.shuffle(shuffled)
        
        # Execute tasks in shuffled order
        results = []
        for idx in shuffled:
            task = tasks[idx]
            try:
                # Process task
                result = await self._process_task(task)
                results.append(result)
            except Exception as e:
                return OrderResult(
                    status=OrderStatus.FAILED,
                    error=str(e)
                )
        
        return OrderResult(
            status=OrderStatus.COMPLETED,
            data={
                "results": results,
                "execution_order": shuffled
            }
        )
    
    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual task"""
        # Mock task processing
        return {
            "task_id": task.get("id"),
            "action": task.get("action"),
            "status": "completed"
        } 