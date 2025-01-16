"""Parallel Order Module"""

from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime

from src.core.agentverse.environment.orders.base import (
    BaseOrder,
    OrderStatus,
    OrderResult
)

class ParallelOrder(BaseOrder):
    """Parallel execution order"""
    
    def __init__(
        self,
        name: str,
        tasks: List[Dict[str, Any]],
        max_workers: int = 3
    ):
        super().__init__(name)
        self.tasks = tasks
        self.max_workers = max_workers
    
    async def execute(self, **kwargs) -> OrderResult:
        """Execute tasks in parallel"""
        try:
            self.status = OrderStatus.RUNNING
            start_time = datetime.utcnow()
            
            # Create task groups
            tasks = []
            for task in self.tasks:
                tasks.append(self._execute_task(task))
            
            # Execute tasks
            results = await asyncio.gather(
                *tasks,
                return_exceptions=True
            )
            
            # Process results
            success = all(
                not isinstance(r, Exception)
                for r in results
            )
            
            # Create result
            self.result = OrderResult(
                status=OrderStatus.COMPLETED if success else OrderStatus.FAILED,
                data={"results": results},
                start_time=start_time,
                end_time=datetime.utcnow()
            )
            self.status = self.result.status
            
            return self.result
            
        except Exception as e:
            self.status = OrderStatus.FAILED
            self.result = OrderResult(
                status=OrderStatus.FAILED,
                error=str(e),
                start_time=start_time,
                end_time=datetime.utcnow()
            )
            return self.result
    
    async def cancel(self) -> None:
        """Cancel parallel execution"""
        self.status = OrderStatus.CANCELLED
    
    async def _execute_task(self, task: Dict[str, Any]) -> Any:
        """Execute single task"""
        action = task.get("action")
        args = task.get("args", {})
        
        # TODO: Implement task execution
        return f"Executed {action}" 