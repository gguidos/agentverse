"""Local Message Bus Implementation"""

from typing import Dict, Any, List, Callable, Optional
from collections import defaultdict
import asyncio
import logging

from src.core.agentverse.message_bus.base import BaseMessageBus
from src.core.agentverse.message_bus.types import MessageTypes

logger = logging.getLogger(__name__)

class LocalMessageBus(BaseMessageBus):
    """In-memory message bus implementation"""
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.connected: bool = False
        self._lock = asyncio.Lock()
    
    async def connect(self) -> None:
        """Connect to local message bus"""
        self.connected = True
        logger.info("Connected to local message bus")
    
    async def disconnect(self) -> None:
        """Disconnect from local message bus"""
        self.connected = False
        self.subscribers.clear()
        logger.info("Disconnected from local message bus")
    
    async def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        message_type: Optional[MessageTypes] = None
    ) -> None:
        """Publish message to topic"""
        if not self.connected:
            raise RuntimeError("Message bus not connected")
            
        async with self._lock:
            handlers = self.subscribers.get(topic, [])
            for handler in handlers:
                try:
                    if message_type:
                        message["type"] = message_type.value
                    await handler(message)
                except Exception as e:
                    logger.error(f"Handler error for topic {topic}: {str(e)}")
    
    async def subscribe(
        self,
        topic: str,
        handler: Callable,
        message_type: Optional[MessageTypes] = None
    ) -> None:
        """Subscribe handler to topic"""
        if not self.connected:
            raise RuntimeError("Message bus not connected")
            
        async with self._lock:
            if handler not in self.subscribers[topic]:
                self.subscribers[topic].append(handler)
                logger.info(f"Subscribed handler to topic: {topic}")
    
    async def unsubscribe(
        self,
        topic: str,
        handler: Optional[Callable] = None
    ) -> None:
        """Unsubscribe handler from topic"""
        if not self.connected:
            raise RuntimeError("Message bus not connected")
            
        async with self._lock:
            if handler:
                if handler in self.subscribers[topic]:
                    self.subscribers[topic].remove(handler)
            else:
                self.subscribers[topic].clear()
            logger.info(f"Unsubscribed from topic: {topic}")
    
    async def get_topics(self) -> List[str]:
        """Get list of active topics"""
        return list(self.subscribers.keys())
    
    async def get_subscribers(self, topic: str) -> List[Callable]:
        """Get subscribers for topic"""
        return self.subscribers.get(topic, []) 