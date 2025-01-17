"""Base Order Module"""

from typing import Dict, Any, Optional, List
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

class OrderStatus(str, Enum):
    """Order execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class OrderConfig(BaseModel):
    """Order configuration"""
    name: str = "default_order"  # Default name
    description: Optional[str] = None
    timeout: float = 30.0
    retry_count: int = 3
    concurrent_limit: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class OrderResult(BaseModel):
    """Order execution result"""
    status: OrderStatus
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None

class BaseOrder:
    """Base class for orders"""
    
    def __init__(self, config: Optional[OrderConfig] = None):
        self.config = config or OrderConfig()
        self.status = OrderStatus.PENDING
        self.result = None
    
    async def execute(self, **kwargs) -> OrderResult:
        """Execute order"""
        raise NotImplementedError
    
    async def cancel(self) -> None:
        """Cancel order execution"""
        self.status = OrderStatus.CANCELLED
    
    def get_status(self) -> OrderStatus:
        """Get current order status"""
        return self.status
    
    def get_result(self) -> Optional[OrderResult]:
        """Get order execution result"""
        return self.result
    
    def reset(self) -> None:
        """Reset order state"""
        self.status = OrderStatus.PENDING
        self.result = None

__all__ = [
    "OrderStatus",
    "OrderConfig",
    "OrderResult",
    "BaseOrder"
] 