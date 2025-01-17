"""Conditional Order Module"""

from typing import Dict, Any, Optional, List, Callable
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

class ConditionalOrderConfig(OrderConfig):
    """Configuration for conditional order"""
    evaluate_all: bool = False  # Whether to evaluate all conditions
    track_branches: bool = True
    default_branch: str = "if_true"
    
    model_config = ConfigDict(
        extra="allow"
    )

@order
class ConditionalOrder(BaseOrder):
    """Conditional execution order"""
    
    name = "conditional_order"
    description = "Executes tasks based on conditions"
    version = "1.0.0"
    
    def __init__(
        self,
        config: Optional[ConditionalOrderConfig] = None,
        condition: Optional[Callable[..., bool]] = None,
        if_true: Optional[BaseOrder] = None,
        if_false: Optional[BaseOrder] = None
    ):
        super().__init__(config or ConditionalOrderConfig())
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false
        self.branch_history = []
    
    async def execute(self, **kwargs) -> OrderResult:
        """Execute conditional order"""
        try:
            start_time = datetime.utcnow()
            self.status = OrderStatus.RUNNING
            
            # Evaluate condition
            result = False
            if self.condition:
                try:
                    result = self.condition(**kwargs)
                except Exception as e:
                    logger.error(f"Condition evaluation failed: {str(e)}")
                    if not self.config.evaluate_all:
                        raise
            
            # Track branch
            branch = "if_true" if result else "if_false"
            if self.config.track_branches:
                self.branch_history.append({
                    "timestamp": datetime.utcnow(),
                    "branch": branch,
                    "condition_result": result
                })
            
            # Execute appropriate branch
            branch_result = None
            if result and self.if_true:
                branch_result = await self.if_true.execute(**kwargs)
            elif not result and self.if_false:
                branch_result = await self.if_false.execute(**kwargs)
            else:
                logger.warning(f"No handler for branch: {branch}")
            
            return OrderResult(
                status=OrderStatus.COMPLETED,
                start_time=start_time,
                end_time=datetime.utcnow(),
                data={
                    "condition_result": result,
                    "executed_branch": branch,
                    "branch_result": branch_result.data if branch_result else None,
                    "branch_history": self.branch_history if self.config.track_branches else None
                }
            )
            
        except Exception as e:
            logger.error(f"Conditional execution failed: {str(e)}")
            return OrderResult(
                status=OrderStatus.FAILED,
                start_time=start_time,
                end_time=datetime.utcnow(),
                error=str(e)
            )
    
    async def cancel(self) -> None:
        """Cancel conditional execution"""
        self.status = OrderStatus.CANCELLED
        if self.if_true and self.if_true.status == OrderStatus.RUNNING:
            await self.if_true.cancel()
        if self.if_false and self.if_false.status == OrderStatus.RUNNING:
            await self.if_false.cancel() 