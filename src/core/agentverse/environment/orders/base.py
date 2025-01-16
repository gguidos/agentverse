"""Base Order Module"""

from abc import ABC, abstractmethod
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

class OrderResult(BaseModel):
    """Order execution result"""
    status: OrderStatus
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None

class BaseOrder(ABC):
    """Base class for orders"""
    
    def __init__(self, name: str):
        self.name = name
        self.status = OrderStatus.PENDING
        self.result = None
    
    @abstractmethod
    async def execute(self, **kwargs) -> OrderResult:
        """Execute order"""
        pass
    
    @abstractmethod
    async def cancel(self) -> None:
        """Cancel order execution"""
        pass 