from typing import Callable, Dict, Any, Optional, List
import asyncio
import json
import logging
from datetime import datetime
from src.core.infrastructure.circuit_breaker import circuit_breaker
from src.core.infrastructure.db.redis_client import RedisClient
from src.core.agentverse.memory.base import Message
from src.core.agentverse.memory.agent_memory import AgentMemoryStore

logger = logging.getLogger(__name__)

class AgentMessageBus:
    """Message bus for agent communication with memory integration"""
    
    def __init__(self, 
                 redis_client: RedisClient,
                 memory_store: Optional[AgentMemoryStore] = None):
        self.redis = redis_client
        self.memory_store = memory_store
        self.subscribers: Dict[str, Callable] = {}
        self.pubsub = None
        self._listener_task = None
        
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    async def publish(self, 
                     topic: str, 
                     message: Dict[str, Any],
                     sender_id: Optional[str] = None,
                     store_in_memory: bool = True) -> bool:
        """Publish message to agents
        
        Args:
            topic: Message topic/channel
            message: Message content
            sender_id: ID of sending agent
            store_in_memory: Whether to persist in memory store
        """
        try:
            # Create message object
            msg = Message(
                content=message.get('content', ''),
                sender=sender_id,
                receiver=topic,
                timestamp=datetime.utcnow(),
                type=message.get('type', 'message'),
                metadata=message.get('metadata', {})
            )
            
            # Store in memory if requested
            if store_in_memory and self.memory_store:
                await self.memory_store.store_memory(
                    topic,
                    {'messages': [msg]},
                    ttl=3600
                )
            
            # Publish to Redis
            await self.redis.publish(
                f"agent:{topic}",
                json.dumps(msg.dict())
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message to {topic}: {str(e)}")
            raise
            
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    async def subscribe(self, 
                       agent_id: str, 
                       callback: Callable[[Message], Any]) -> None:
        """Subscribe agent to messages
        
        Args:
            agent_id: ID of subscribing agent
            callback: Function to handle received messages
        """
        try:
            self.subscribers[agent_id] = callback
            
            if not self.pubsub:
                self.pubsub = self.redis.pubsub()
                
            await self.pubsub.subscribe(f"agent:{agent_id}")
            
            # Start listener if not running
            if not self._listener_task or self._listener_task.done():
                self._listener_task = asyncio.create_task(self._message_listener())
                
        except Exception as e:
            logger.error(f"Failed to subscribe agent {agent_id}: {str(e)}")
            raise
            
    async def unsubscribe(self, agent_id: str) -> None:
        """Unsubscribe agent from messages"""
        try:
            if agent_id in self.subscribers:
                del self.subscribers[agent_id]
                
            if self.pubsub:
                await self.pubsub.unsubscribe(f"agent:{agent_id}")
                
        except Exception as e:
            logger.error(f"Failed to unsubscribe agent {agent_id}: {str(e)}")
            
    async def _message_listener(self) -> None:
        """Background task to listen for messages"""
        try:
            while True:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                if message and message['type'] == 'message':
                    # Parse message
                    data = json.loads(message['data'])
                    msg = Message(**data)
                    
                    # Get subscriber
                    channel = message['channel'].decode('utf-8')
                    agent_id = channel.split(':')[1]
                    
                    if agent_id in self.subscribers:
                        try:
                            await self.subscribers[agent_id](msg)
                        except Exception as e:
                            logger.error(f"Error in subscriber callback for {agent_id}: {str(e)}")
                            
                await asyncio.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Error in message listener: {str(e)}")
            # Restart listener
            self._listener_task = asyncio.create_task(self._message_listener())
            
    async def close(self) -> None:
        """Clean up resources"""
        try:
            if self._listener_task:
                self._listener_task.cancel()
                
            if self.pubsub:
                await self.pubsub.close()
                
        except Exception as e:
            logger.error(f"Error closing message bus: {str(e)}")
            
    async def health_check(self) -> bool:
        """Check if message bus is healthy"""
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False 