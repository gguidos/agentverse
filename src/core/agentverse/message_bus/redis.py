"""
Redis-based message bus implementation
"""

import json
import logging
from typing import Any, Dict, Optional
from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.core.agentverse.message_bus.base import BaseMessageBus
from src.core.agentverse.exceptions import MessageBusError

logger = logging.getLogger(__name__)

class RedisMessageBus(BaseMessageBus):
    """Redis implementation of message bus"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        **kwargs
    ):
        """Initialize Redis connection
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Optional Redis password
            **kwargs: Additional Redis connection arguments
        """
        self.redis: Optional[Redis] = None
        self.connection_params = {
            "host": host,
            "port": port,
            "db": db,
            "password": password,
            **kwargs
        }
    
    async def connect(self) -> None:
        """Connect to Redis"""
        try:
            self.redis = Redis(**self.connection_params)
            await self.redis.ping()
            logger.info("Connected to Redis")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise MessageBusError(f"Redis connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Disconnected from Redis")
    
    async def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """Publish message to channel"""
        if not self.redis:
            raise MessageBusError("Not connected to Redis")
            
        try:
            message_json = json.dumps(message)
            await self.redis.publish(channel, message_json)
            logger.debug(f"Published message to {channel}")
        except RedisError as e:
            logger.error(f"Failed to publish message: {e}")
            raise MessageBusError(f"Redis publish failed: {e}")
    
    async def subscribe(self, channel: str) -> None:
        """Subscribe to channel"""
        if not self.redis:
            raise MessageBusError("Not connected to Redis")
            
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(channel)
            logger.info(f"Subscribed to {channel}")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        payload = json.loads(message["data"])
                        await self._handle_message(channel, payload)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message: {e}")
                    except Exception as e:
                        logger.error(f"Error handling message: {e}")
                        
        except RedisError as e:
            logger.error(f"Subscription error: {e}")
            raise MessageBusError(f"Redis subscription failed: {e}") 