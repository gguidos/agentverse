from typing import Dict, Any
from src.core.infrastructure.circuit_breaker import circuit_breaker

class AgentMemoryStore:
    """Persistent memory store for agents"""
    
    def __init__(self, mongo_client, redis_client):
        self.mongo = mongo_client
        self.redis = redis_client
    
    @circuit_breaker(failure_threshold=3)
    async def store_memory(self, agent_id: str, memory: Dict[str, Any]):
        """Store agent memory with caching"""
        await self.redis.set(f"memory:{agent_id}", memory, ex=3600)
        await self.mongo.insert_one({
            "agent_id": agent_id,
            "memory": memory,
            "timestamp": datetime.utcnow()
        }) 