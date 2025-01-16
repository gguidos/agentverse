"""Message Factory Module"""

from typing import Dict, Any, Optional
from pydantic import Field

from src.core.agentverse.factories.base import BaseFactory, FactoryConfig
from src.core.agentverse.entities.message import Message, MessageConfig

class MessageFactoryConfig(FactoryConfig):
    """Message factory configuration"""
    sender: str
    recipient: str
    content: Dict[str, Any] = Field(default_factory=dict)
    priority: str = "normal"

class MessageFactory(BaseFactory[Message]):
    """Factory for creating messages"""
    
    @classmethod
    async def create(
        cls,
        config: MessageFactoryConfig,
        **kwargs
    ) -> Message:
        """Create a message instance"""
        if not await cls.validate_config(config):
            raise ValueError("Invalid message configuration")
            
        message_config = MessageConfig(
            id=kwargs.get("id"),
            type=config.type,
            name=config.name,
            sender=config.sender,
            recipient=config.recipient,
            content=config.content,
            priority=config.priority,
            metadata=config.metadata
        )
        
        return Message(config=message_config)
    
    @classmethod
    async def validate_config(
        cls,
        config: MessageFactoryConfig
    ) -> bool:
        """Validate message factory configuration"""
        if not config.sender or not config.recipient:
            return False
        valid_priorities = ["low", "normal", "high", "urgent"]
        if config.priority not in valid_priorities:
            return False
        return True
    
    @classmethod
    def get_defaults(cls) -> Dict[str, Any]:
        """Get default message configuration"""
        return {
            "type": "default",
            "priority": "normal",
            "content": {}
        } 