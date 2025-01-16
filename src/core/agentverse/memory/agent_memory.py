from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import logging
from src.core.infrastructure.circuit_breaker import circuit_breaker
from src.core.agentverse.memory.base import Message
from src.core.infrastructure.db.redis_client import RedisClient
from src.core.infrastructure.db.mongo_client import MongoDBClient

logger = logging.getLogger(__name__)

class AgentMemoryStore:
    """Persistent memory store for agents with caching"""
    
    def __init__(self, mongo_client: MongoDBClient, redis_client: RedisClient):
        self.mongo = mongo_client
        self.redis = redis_client
        
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    async def store_memory(self, agent_id: str, memory: Dict[str, Any], ttl: int = 3600) -> bool:
        """Store agent memory with caching
        
        Args:
            agent_id: Unique identifier for the agent
            memory: Memory data to store
            ttl: Time-to-live for cache in seconds
        """
        try:
            # Convert Message objects to dict for storage
            if isinstance(memory.get('messages'), list):
                memory['messages'] = [
                    msg.dict() if isinstance(msg, Message) else msg 
                    for msg in memory['messages']
                ]
            
            # Store in Redis cache
            await self.redis.set(
                f"memory:{agent_id}",
                json.dumps(memory),
                ex=ttl
            )
            
            # Store in MongoDB
            await self.mongo.insert_one({
                "agent_id": agent_id,
                "memory": memory,
                "timestamp": datetime.utcnow()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store memory for agent {agent_id}: {str(e)}")
            raise
            
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    async def get_memory(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve agent memory with caching"""
        try:
            # Try cache first
            cached = await self.redis.get(f"memory:{agent_id}")
            if cached:
                memory = json.loads(cached)
            else:
                # Fall back to MongoDB
                result = await self.mongo.find_one({"agent_id": agent_id})
                if not result:
                    return None
                memory = result["memory"]
                
                # Update cache
                await self.redis.set(
                    f"memory:{agent_id}",
                    json.dumps(memory),
                    ex=3600
                )
            
            # Convert stored dicts back to Message objects
            if isinstance(memory.get('messages'), list):
                memory['messages'] = [
                    Message(**msg) if isinstance(msg, dict) else msg
                    for msg in memory['messages']
                ]
                
            return memory
            
        except Exception as e:
            logger.error(f"Failed to retrieve memory for agent {agent_id}: {str(e)}")
            raise
            
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    async def clear_memory(self, agent_id: str) -> bool:
        """Clear agent memory from both cache and persistent storage"""
        try:
            # Clear from Redis
            await self.redis.delete(f"memory:{agent_id}")
            
            # Clear from MongoDB
            await self.mongo.delete_many({"agent_id": agent_id})
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear memory for agent {agent_id}: {str(e)}")
            raise
            
    async def health_check(self) -> Dict[str, bool]:
        """Check health of memory store dependencies"""
        status = {
            "redis": False,
            "mongo": False
        }
        
        try:
            # Check Redis
            await self.redis.ping()
            status["redis"] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            
        try:
            # Check MongoDB
            await self.mongo.command("ping")
            status["mongo"] = True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {str(e)}")
            
        return status 