from typing import Callable
import asyncio

class AgentMessageBus:
    """Message bus for agent communication"""
    def __init__(self, redis_client):
        self.redis = redis_client
        self.subscribers = {}
        
    async def publish(self, topic: str, message: dict):
        """Publish message to agents"""
        await self.redis.publish(f"agent:{topic}", message)
        
    async def subscribe(self, agent_id: str, callback: Callable):
        """Subscribe agent to messages"""
        self.subscribers[agent_id] = callback
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"agent:{agent_id}") 