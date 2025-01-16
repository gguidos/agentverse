from typing import Dict, Any, Optional, List, Callable, Union
from pydantic import BaseModel, Field, ConfigDict
from abc import ABC, abstractmethod
import logging

from src.core.agentverse.exceptions import MessageBusError

logger = logging.getLogger(__name__)

class BusConfig(BaseModel):
    """Base configuration for message bus"""
    name: str = "default"
    persistence: bool = True
    max_queue: int = 1000
    timeout: int = 30
    retry_enabled: bool = True
    max_retries: int = 3
    
    model_config = ConfigDict(
        extra="allow"
    )

class Message(BaseModel):
    """Base message model"""
    id: str
    type: str
    topic: str
    content: Dict[str, Any]
    timestamp: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class BaseMessageBus(ABC):
    """Base class for message bus implementations"""
    
    def __init__(self, config: Optional[BusConfig] = None):
        """Initialize message bus
        
        Args:
            config: Optional bus configuration
        """
        self.config = config or BusConfig()
    
    @abstractmethod
    async def connect(self) -> None:
        """Connect to message bus
        
        Raises:
            MessageBusError: If connection fails
        """
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
        **kwargs
    ) -> None:
        """Publish message to topic
        
        Args:
            topic: Message topic
            message: Message content
            **kwargs: Additional arguments
            
        Raises:
            MessageBusError: If publish fails
        """
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        handler: Callable,
        **kwargs
    ) -> None:
        """Subscribe to topic
        
        Args:
            topic: Topic pattern to subscribe to
            handler: Message handler function
            **kwargs: Additional arguments
            
        Raises:
            MessageBusError: If subscription fails
        """
        pass
    
    @abstractmethod
    async def unsubscribe(
        self,
        topic: str,
        handler: Optional[Callable] = None
    ) -> None:
        """Unsubscribe from topic
        
        Args:
            topic: Topic to unsubscribe from
            handler: Optional specific handler to remove
            
        Raises:
            MessageBusError: If unsubscribe fails
        """
        pass
    
    async def publish_batch(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> None:
        """Publish multiple messages
        
        Args:
            messages: List of (topic, message) pairs
            **kwargs: Additional arguments
            
        Raises:
            MessageBusError: If batch publish fails
        """
        try:
            for topic, message in messages:
                await self.publish(topic, message, **kwargs)
                
        except Exception as e:
            logger.error(f"Batch publish failed: {str(e)}")
            raise MessageBusError(f"Failed to publish batch: {str(e)}")
    
    async def subscribe_multiple(
        self,
        subscriptions: List[Dict[str, Any]],
        **kwargs
    ) -> None:
        """Subscribe to multiple topics
        
        Args:
            subscriptions: List of (topic, handler) pairs
            **kwargs: Additional arguments
            
        Raises:
            MessageBusError: If batch subscribe fails
        """
        try:
            for topic, handler in subscriptions:
                await self.subscribe(topic, handler, **kwargs)
                
        except Exception as e:
            logger.error(f"Batch subscribe failed: {str(e)}")
            raise MessageBusError(f"Failed to subscribe batch: {str(e)}")
    
    def create_topic_handler(
        self,
        topic: str
    ) -> Callable:
        """Create decorator for topic handler
        
        Args:
            topic: Topic to handle
            
        Returns:
            Handler decorator
        """
        def decorator(func: Callable) -> Callable:
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            
            # Register handler
            self.subscribe(topic, wrapper)
            return wrapper
            
        return decorator
    
    async def _validate_topic(
        self,
        topic: str
    ) -> None:
        """Validate topic string
        
        Args:
            topic: Topic to validate
            
        Raises:
            MessageBusError: If topic is invalid
        """
        if not isinstance(topic, str) or not topic:
            raise MessageBusError(
                message="Invalid topic",
                details={"topic": topic}
            )
    
    async def _validate_message(
        self,
        message: Dict[str, Any]
    ) -> None:
        """Validate message content
        
        Args:
            message: Message to validate
            
        Raises:
            MessageBusError: If message is invalid
        """
        if not isinstance(message, dict):
            raise MessageBusError(
                message="Invalid message format",
                details={"type": type(message)}
            )
    
    async def _validate_handler(
        self,
        handler: Callable
    ) -> None:
        """Validate message handler
        
        Args:
            handler: Handler to validate
            
        Raises:
            MessageBusError: If handler is invalid
        """
        if not callable(handler):
            raise MessageBusError(
                message="Invalid message handler",
                details={"type": type(handler)}
            ) 