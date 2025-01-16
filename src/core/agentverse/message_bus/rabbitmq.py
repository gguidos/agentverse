from typing import Dict, Any, Optional, List, Callable, Union
from pydantic import BaseModel, Field
import aio_pika
import json
import logging
from functools import wraps

from src.core.agentverse.message_bus.base import BaseMessageBus, BusConfig
from src.core.agentverse.exceptions import MessageBusError

logger = logging.getLogger(__name__)

class RabbitMQConfig(BusConfig):
    """RabbitMQ configuration"""
    url: str = "amqp://guest:guest@localhost:5672/"
    exchange: str = "agentverse"
    queue_prefix: str = "agentverse."
    durable: bool = True
    auto_delete: bool = False
    persistent: bool = True
    retry_interval: int = 5
    max_retries: int = 3

class RabbitMQBus(BaseMessageBus):
    """RabbitMQ-based message bus implementation"""
    
    def __init__(self, config: Optional[RabbitMQConfig] = None):
        """Initialize RabbitMQ bus"""
        super().__init__()
        self.config = config or RabbitMQConfig()
        self._connection = None
        self._channel = None
        self._exchange = None
        self._subscribers: Dict[str, List[Callable]] = {}
    
    async def connect(self) -> None:
        """Connect to RabbitMQ"""
        try:
            # Create connection
            self._connection = await aio_pika.connect_robust(
                self.config.url,
                retry_interval=self.config.retry_interval
            )
            
            # Create channel
            self._channel = await self._connection.channel()
            
            # Declare exchange
            self._exchange = await self._channel.declare_exchange(
                self.config.exchange,
                aio_pika.ExchangeType.TOPIC,
                durable=self.config.durable
            )
            
            logger.info(f"Connected to RabbitMQ: {self.config.url}")
            
        except Exception as e:
            logger.error(f"RabbitMQ connection failed: {str(e)}")
            raise MessageBusError(f"Failed to connect to RabbitMQ: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ"""
        try:
            if self._connection:
                await self._connection.close()
                self._connection = None
                self._channel = None
                self._exchange = None
                
        except Exception as e:
            logger.error(f"RabbitMQ disconnect failed: {str(e)}")
    
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
        """
        try:
            if not self._exchange:
                await self.connect()
            
            # Create message
            message_body = json.dumps(message).encode()
            rabbit_message = aio_pika.Message(
                message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                **kwargs
            )
            
            # Publish message
            await self._exchange.publish(
                rabbit_message,
                routing_key=topic
            )
            
            logger.debug(f"Published message to {topic}: {message}")
            
        except Exception as e:
            logger.error(f"RabbitMQ publish failed: {str(e)}")
            raise MessageBusError(f"Failed to publish message: {str(e)}")
    
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
        """
        try:
            if not self._channel:
                await self.connect()
            
            # Create queue
            queue_name = f"{self.config.queue_prefix}{topic}"
            queue = await self._channel.declare_queue(
                queue_name,
                durable=self.config.durable,
                auto_delete=self.config.auto_delete
            )
            
            # Bind queue to exchange
            await queue.bind(
                self._exchange,
                routing_key=topic
            )
            
            # Create message handler
            async def message_handler(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        # Parse message
                        body = json.loads(message.body.decode())
                        
                        # Call handler
                        await handler(body)
                        
                    except Exception as e:
                        logger.error(f"Message handler failed: {str(e)}")
                        # Reject message on error
                        await message.reject(requeue=False)
            
            # Start consuming
            await queue.consume(message_handler)
            
            # Store subscriber
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(handler)
            
            logger.info(f"Subscribed to {topic}")
            
        except Exception as e:
            logger.error(f"RabbitMQ subscribe failed: {str(e)}")
            raise MessageBusError(f"Failed to subscribe: {str(e)}")
    
    async def unsubscribe(
        self,
        topic: str,
        handler: Optional[Callable] = None
    ) -> None:
        """Unsubscribe from topic
        
        Args:
            topic: Topic to unsubscribe from
            handler: Optional specific handler to remove
        """
        try:
            if topic in self._subscribers:
                if handler:
                    self._subscribers[topic].remove(handler)
                else:
                    del self._subscribers[topic]
                
            # Delete queue
            queue_name = f"{self.config.queue_prefix}{topic}"
            await self._channel.declare_queue(
                queue_name,
                auto_delete=True
            )
            
            logger.info(f"Unsubscribed from {topic}")
            
        except Exception as e:
            logger.error(f"RabbitMQ unsubscribe failed: {str(e)}")
            raise MessageBusError(f"Failed to unsubscribe: {str(e)}") 