"""
Message bus implementations
"""

from typing import Dict, List, Optional, Set, Any
from src.core.agentverse.message import Message
from src.core.agentverse.exceptions import MessageBusError

class BaseMessageBus:
    """Base message bus interface"""
    
    async def subscribe(self, topic: str, subscriber: str) -> None:
        """Subscribe to topic"""
        pass
        
    async def unsubscribe(self, topic: str, subscriber: str) -> None:
        """Unsubscribe from topic"""
        pass
        
    async def publish(self, topic: str, message: Message) -> None:
        """Publish message to topic"""
        pass
        
    async def get_subscribers(self, topic: str) -> List[str]:
        """Get subscribers for topic"""
        pass
        
    async def get_topics(self) -> List[str]:
        """Get all topics"""
        pass

class InMemoryMessageBus(BaseMessageBus):
    """In-memory message bus implementation"""
    
    def __init__(self):
        self.topics: Dict[str, Set[str]] = {}
        self.messages: Dict[str, List[Message]] = {}
    
    async def subscribe(self, topic: str, subscriber: str) -> None:
        """Subscribe to topic"""
        if not topic or not subscriber:
            raise MessageBusError("Invalid topic or subscriber")
            
        if topic not in self.topics:
            self.topics[topic] = set()
            self.messages[topic] = []
            
        self.topics[topic].add(subscriber)
    
    async def unsubscribe(self, topic: str, subscriber: str) -> None:
        """Unsubscribe from topic"""
        if topic in self.topics:
            self.topics[topic].discard(subscriber)
    
    async def publish(self, topic: str, message: Message) -> None:
        """Publish message to topic"""
        if not topic or not message:
            raise MessageBusError("Invalid topic or message")
            
        if topic not in self.messages:
            self.messages[topic] = []
            
        self.messages[topic].append(message)
    
    async def get_subscribers(self, topic: str) -> List[str]:
        """Get subscribers for topic"""
        return list(self.topics.get(topic, set()))
    
    async def get_topics(self) -> List[str]:
        """Get all topics"""
        return list(self.topics.keys())

class MessageBus:
    """Message bus for agent communication"""
    
    def __init__(
        self,
        transport_type: str = "memory",
        host: Optional[str] = None,
        port: Optional[int] = None,
        channel_capacity: int = 100,
        delivery_guarantee: str = "at_least_once"
    ):
        self.transport_type = transport_type
        self.host = host
        self.port = port
        self.channel_capacity = channel_capacity
        self.delivery_guarantee = delivery_guarantee
        
    async def enable_persistence(self, storage_path: str) -> None:
        """Enable message persistence"""
        pass

# Default message bus instance
message_bus = InMemoryMessageBus()

__all__ = [
    "BaseMessageBus",
    "InMemoryMessageBus",
    "message_bus"
] 