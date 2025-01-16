"""Base Message Bus Module"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
from src.core.agentverse.message_bus.types import MessageTypes

class BaseMessageBus(ABC):
    """Abstract base class for message bus implementations"""
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to message bus"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from message bus"""
        pass
    
    @abstractmethod
    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        message_type: Optional[MessageTypes] = None
    ) -> None:
        """Publish message to topic
        
        Args:
            topic: Message topic
            message: Message payload
            message_type: Optional message type
        """
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        handler: Callable,
        message_type: Optional[MessageTypes] = None
    ) -> None:
        """Subscribe handler to topic
        
        Args:
            topic: Topic to subscribe to
            handler: Message handler callback
            message_type: Optional message type filter
        """
        pass
    
    @abstractmethod
    async def unsubscribe(
        self,
        topic: str,
        handler: Optional[Callable] = None
    ) -> None:
        """Unsubscribe handler from topic
        
        Args:
            topic: Topic to unsubscribe from
            handler: Optional specific handler to remove
        """
        pass
    
    @abstractmethod
    async def get_topics(self) -> List[str]:
        """Get list of active topics
        
        Returns:
            List of topic strings
        """
        pass
    
    @abstractmethod
    async def get_subscribers(self, topic: str) -> List[Callable]:
        """Get subscribers for topic
        
        Args:
            topic: Topic to get subscribers for
            
        Returns:
            List of subscriber handlers
        """
        pass 