"""Random Order Module"""

from typing import Dict, Any, Optional, List
import random
import asyncio
from datetime import datetime

from src.core.agentverse.environment.orders.base import (
    BaseOrder,
    OrderStatus,
    OrderResult
)

class RandomOrder(BaseOrder):
    """Random execution order"""
    
    def __init__(
        self,
        name: str,
        tasks: List[Dict[str, Any]],
        seed: Optional[int] = None
    ):
        """Initialize random order
        
        Args:
            name: Order name
            tasks: List of tasks to execute
            seed: Optional random seed
        """
        super().__init__(name)
        self.tasks = tasks
        if seed is not None:
            random.seed(seed)
    
    async def execute(self, **kwargs) -> OrderResult:
        """Execute tasks in random order"""
        try:
            self.status = OrderStatus.RUNNING
            start_time = datetime.utcnow()
            
            # Randomize task order
            tasks = self.tasks.copy()
            random.shuffle(tasks)
            
            # Execute tasks sequentially in random order
            results = []
            for task in tasks:
                try:
                    result = await self._execute_task(task)
                    results.append({
                        "task": task,
                        "result": result,
                        "success": True
                    })
                except Exception as e:
                    results.append({
                        "task": task,
                        "error": str(e),
                        "success": False
                    })
            
            # Check if all tasks succeeded
            success = all(r["success"] for r in results)
            
            # Create result
            self.result = OrderResult(
                status=OrderStatus.COMPLETED if success else OrderStatus.FAILED,
                data={
                    "results": results,
                    "execution_order": [t.get("action") for t in tasks]
                },
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
        """Cancel random execution"""
        self.status = OrderStatus.CANCELLED
    
    async def _execute_task(self, task: Dict[str, Any]) -> Any:
        """Execute single task
        
        Args:
            task: Task configuration
            
        Returns:
            Task result
        """
        action = task.get("action")
        args = task.get("args", {})
        delay = task.get("delay", 0)
        
        # Simulate task execution with optional delay
        if delay:
            await asyncio.sleep(delay)
            
        # TODO: Implement actual task execution
        return f"Executed {action} with args {args}" 