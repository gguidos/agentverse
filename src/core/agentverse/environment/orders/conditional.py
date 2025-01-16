"""Conditional Order Module"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from src.core.agentverse.environment.orders.base import (
    BaseOrder,
    OrderStatus,
    OrderResult
)

class ConditionalOrder(BaseOrder):
    """Conditional execution order"""
    
    def __init__(
        self,
        name: str,
        condition: Callable[..., bool],
        if_true: BaseOrder,
        if_false: Optional[BaseOrder] = None
    ):
        super().__init__(name)
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false
    
    async def execute(self, **kwargs) -> OrderResult:
        """Execute conditional order"""
        try:
            self.status = OrderStatus.RUNNING
            start_time = datetime.utcnow()
            
            # Evaluate condition
            should_execute = self.condition(**kwargs)
            
            # Execute appropriate order
            if should_execute:
                result = await self.if_true.execute(**kwargs)
            elif self.if_false:
                result = await self.if_false.execute(**kwargs)
            else:
                result = OrderResult(
                    status=OrderStatus.COMPLETED,
                    data={"skipped": True},
                    start_time=start_time,
                    end_time=datetime.utcnow()
                )
            
            self.result = result
            self.status = result.status
            return result
            
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
        """Cancel conditional execution"""
        self.status = OrderStatus.CANCELLED
        if self.if_true and self.if_true.status == OrderStatus.RUNNING:
            await self.if_true.cancel()
        if self.if_false and self.if_false.status == OrderStatus.RUNNING:
            await self.if_false.cancel() 