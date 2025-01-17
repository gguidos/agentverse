"""Parallel Order Module"""

from typing import Dict, Any, Optional, List
from pydantic import Field, ConfigDict
from datetime import datetime
import asyncio
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

class ParallelOrderConfig(OrderConfig):
    """Configuration for parallel order"""
    max_workers: int = 3
    timeout: float = 30.0
    retry_failed: bool = True
    max_retries: int = 3
    
    model_config = ConfigDict(
        extra="allow"
    )

@order
class ParallelOrder(BaseOrder):
    """Parallel execution order"""
    
    name = "parallel_order"
    description = "Executes tasks in parallel"
    version = "1.0.0"
    
    def __init__(self, config: Optional[ParallelOrderConfig] = None):
        super().__init__(config or ParallelOrderConfig())
        self.active_tasks = set()
        self.completed_tasks = set()
        self.failed_tasks = set()
    
    async def execute(self, **kwargs) -> OrderResult:
        """Execute tasks in parallel"""
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
            
            # Create task groups
            results = []
            async with asyncio.TaskGroup() as group:
                task_futures = [
                    group.create_task(self._execute_task(task))
                    for task in tasks[:self.config.max_workers]
                ]
                
                # Wait for tasks
                for future in asyncio.as_completed(task_futures):
                    try:
                        result = await future
                        results.append(result)
                        self.completed_tasks.add(id(result))
                    except Exception as e:
                        logger.error(f"Task execution failed: {str(e)}")
                        if self.config.retry_failed:
                            # Add to retry queue
                            self.failed_tasks.add(id(future))
            
            # Handle retries if needed
            if self.failed_tasks and self.config.retry_failed:
                retry_results = await self._handle_retries()
                results.extend(retry_results)
            
            return OrderResult(
                status=OrderStatus.COMPLETED,
                start_time=start_time,
                end_time=datetime.utcnow(),
                data={
                    "results": results,
                    "completed": len(self.completed_tasks),
                    "failed": len(self.failed_tasks)
                }
            )
            
        except Exception as e:
            logger.error(f"Parallel execution failed: {str(e)}")
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
    
    async def _handle_retries(self) -> List[Any]:
        """Handle failed task retries"""
        retry_results = []
        retry_count = 0
        
        while self.failed_tasks and retry_count < self.config.max_retries:
            retry_count += 1
            current_failed = self.failed_tasks.copy()
            self.failed_tasks.clear()
            
            for task_id in current_failed:
                try:
                    result = await self._execute_task({"id": task_id})
                    retry_results.append(result)
                    self.completed_tasks.add(task_id)
                except Exception as e:
                    logger.error(f"Retry {retry_count} failed for task {task_id}: {str(e)}")
                    self.failed_tasks.add(task_id)
        
        return retry_results 