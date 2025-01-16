"""Order Manager Module"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import logging

from src.core.agentverse.environment.orders.base import (
    BaseOrder,
    OrderStatus,
    OrderResult
)

logger = logging.getLogger(__name__)

class OrderManager:
    """Order execution manager"""
    
    def __init__(self):
        self.active_orders: Dict[str, BaseOrder] = {}
    
    async def __aenter__(self):
        """Context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.cancel_all()
    
    async def execute(
        self,
        order: BaseOrder,
        **kwargs
    ) -> OrderResult:
        """Execute order
        
        Args:
            order: Order to execute
            **kwargs: Execution arguments
            
        Returns:
            Execution result
        """
        try:
            # Register order
            self.active_orders[order.name] = order
            
            # Execute order
            result = await order.execute(**kwargs)
            
            # Cleanup
            if order.name in self.active_orders:
                del self.active_orders[order.name]
                
            return result
            
        except Exception as e:
            logger.error(f"Order execution failed: {str(e)}")
            if order.name in self.active_orders:
                del self.active_orders[order.name]
            raise
    
    async def cancel(self, order_name: str) -> None:
        """Cancel order execution
        
        Args:
            order_name: Name of order to cancel
        """
        if order_name in self.active_orders:
            order = self.active_orders[order_name]
            await order.cancel()
            del self.active_orders[order_name]
    
    async def cancel_all(self) -> None:
        """Cancel all active orders"""
        for order_name in list(self.active_orders.keys()):
            await self.cancel(order_name) 