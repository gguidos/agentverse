"""Message Entity Module"""

from typing import Dict, Any, Optional
from pydantic import Field

from src.core.agentverse.entities.base import (
    BaseEntity,
    EntityConfig,
    EntityState
)

class MessageState(EntityState):
    """Message state model"""
    status: str = "created"
    delivered: bool = False
    read: bool = False

class MessageConfig(EntityConfig):
    """Message configuration"""
    sender: str
    recipient: str
    content: Dict[str, Any] = Field(default_factory=dict)
    priority: str = "normal"

class Message(BaseEntity):
    """Message entity implementation"""
    
    def __init__(self, config: MessageConfig):
        super().__init__(config)
        self.state = MessageState()
    
    async def update(self, updates: Dict[str, Any]) -> None:
        """Update message state"""
        await super().update(updates)
        
        if "status" in updates:
            self.state.status = updates["status"]
        if "delivered" in updates:
            self.state.delivered = updates["delivered"]
        if "read" in updates:
            self.state.read = updates["read"]
    
    async def validate(self) -> bool:
        """Validate message state"""
        if not self.config.sender or not self.config.recipient:
            return False
        return True 