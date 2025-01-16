from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging
from src.core.infrastructure.db.redis_client import RedisClient
from src.core.infrastructure.db.mongo_client import MongoDBClient
from src.core.agentverse.memory.base import Message

logger = logging.getLogger(__name__)

class AgentMemoryManager:
    """Manages agent memory with different storage strategies"""
    
    def __init__(self, short_term: RedisClient, long_term: MongoDBClient):
        self.short_term = short_term
        self.long_term = long_term
        
    async def store(self, 
                   agent_id: str, 
                   memory: Dict[str, Any], 
                   memory_type: str = "short_term") -> bool:
        """Store memory in specified storage"""
        try:
            if memory_type == "short_term":
                return await self._store_short_term(agent_id, memory)
            else:
                return await self._store_long_term(agent_id, memory)
        except Exception as e:
            logger.error(f"Failed to store memory: {str(e)}")
            return False

    async def retrieve(self, 
                      agent_id: str, 
                      memory_type: str = "short_term") -> Optional[Dict[str, Any]]:
        """Retrieve memory from specified storage"""
        try:
            if memory_type == "short_term":
                return await self._retrieve_short_term(agent_id)
            else:
                return await self._retrieve_long_term(agent_id)
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {str(e)}")
            return None

    async def _store_short_term(self, agent_id: str, memory: Dict[str, Any]) -> bool:
        """Store memory in Redis"""
        try:
            key = f"memory:{agent_id}"
            # Convert Message objects to dict for storage
            if isinstance(memory.get('messages'), list):
                memory['messages'] = [
                    msg.dict() if isinstance(msg, Message) else msg 
                    for msg in memory['messages']
                ]
            await self.short_term.set(key, json.dumps(memory), ex=3600)
            return True
        except Exception as e:
            logger.error(f"Failed to store short-term memory: {str(e)}")
            return False

    async def _store_long_term(self, agent_id: str, memory: Dict[str, Any]) -> bool:
        """Store memory in MongoDB"""
        try:
            # Convert Message objects to dict for storage
            if isinstance(memory.get('messages'), list):
                memory['messages'] = [
                    msg.dict() if isinstance(msg, Message) else msg 
                    for msg in memory['messages']
                ]
            await self.long_term.insert_one({
                "agent_id": agent_id,
                "memory": memory,
                "timestamp": datetime.utcnow()
            })
            return True
        except Exception as e:
            logger.error(f"Failed to store long-term memory: {str(e)}")
            return False

    async def _retrieve_short_term(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve memory from Redis"""
        try:
            key = f"memory:{agent_id}"
            data = await self.short_term.get(key)
            if data:
                memory = json.loads(data)
                # Convert stored dicts back to Message objects
                if isinstance(memory.get('messages'), list):
                    memory['messages'] = [
                        Message(**msg) if isinstance(msg, dict) else msg
                        for msg in memory['messages']
                    ]
                return memory
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve short-term memory: {str(e)}")
            return None

    async def _retrieve_long_term(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve memory from MongoDB"""
        try:
            result = await self.long_term.find_one({"agent_id": agent_id})
            if result:
                memory = result["memory"]
                # Convert stored dicts back to Message objects
                if isinstance(memory.get('messages'), list):
                    memory['messages'] = [
                        Message(**msg) if isinstance(msg, dict) else msg
                        for msg in memory['messages']
                    ]
                return memory
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve long-term memory: {str(e)}")
            return None 