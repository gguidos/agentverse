"""Sequential Order Module"""

from typing import Dict, Any, Optional, List
from pydantic import Field, ConfigDict
from datetime import datetime
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

class SequentialOrderConfig(OrderConfig):
    """Configuration for sequential order"""
    skip_unavailable: bool = True
    track_skips: bool = True
    allow_reverse: bool = False
    batch_size: int = 1
    min_batch_size: int = 1
    
    model_config = ConfigDict(
        extra="allow"
    )

@order
class SequentialOrder(BaseOrder):
    """Sequential execution order"""
    
    name = "sequential_order"
    description = "Executes tasks sequentially"
    version = "1.0.0"
    
    def __init__(self, config: Optional[SequentialOrderConfig] = None):
        super().__init__(config or SequentialOrderConfig())
        self.current_index = 0
        self.skipped_indices = set()
    
    async def execute(self, **kwargs) -> OrderResult:
        """Execute tasks sequentially"""
        try:
            start_time = datetime.utcnow()
            self.status = OrderStatus.RUNNING
            
            tasks = kwargs.get("tasks", [])
            if not tasks:
                return OrderResult(
                    status=OrderStatus.COMPLETED,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    data={"message": "No tasks to execute"}
                )
            
            results = []
            while self.current_index < len(tasks):
                # Get next batch
                batch_end = min(
                    self.current_index + self.config.batch_size,
                    len(tasks)
                )
                batch = tasks[self.current_index:batch_end]
                
                # Execute batch
                for task in batch:
                    if self.status == OrderStatus.CANCELLED:
                        break
                        
                    try:
                        result = await self._execute_task(task)
                        results.append(result)
                    except Exception as e:
                        if not self.config.skip_unavailable:
                            raise
                        logger.warning(f"Skipping failed task: {str(e)}")
                        self.skipped_indices.add(self.current_index)
                        
                    self.current_index += 1
                
                if self.status == OrderStatus.CANCELLED:
                    break
            
            status = (
                OrderStatus.CANCELLED if self.status == OrderStatus.CANCELLED
                else OrderStatus.COMPLETED
            )
            
            return OrderResult(
                status=status,
                start_time=start_time,
                end_time=datetime.utcnow(),
                data={
                    "results": results,
                    "completed": self.current_index,
                    "skipped": len(self.skipped_indices)
                }
            )
            
        except Exception as e:
            logger.error(f"Sequential execution failed: {str(e)}")
            return OrderResult(
                status=OrderStatus.FAILED,
                start_time=start_time,
                end_time=datetime.utcnow(),
                error=str(e)
            )
    
    async def _execute_task(self, task: Dict[str, Any]) -> Any:
        """Execute single task"""
        # Implementation depends on task type
        return {"task_id": task.get("id"), "status": "completed"} 