from typing import List, Dict
from src.core.agentverse.memory.base import BaseMemory, Message
from src.core.agentverse.memory.registry import memory_registry

@memory_registry.register("persistent")
class PersistentMemory(BaseMemory):
    """MongoDB-backed persistent memory"""
    
    def __init__(self, mongo_client):
        super().__init__()
        self.db = mongo_client
        
    async def add_message(self, messages: List[Message]) -> None:
        """Add messages to persistent storage"""
        await self.db.insert_many([
            m.dict() for m in messages
        ])
        self.messages.extend(messages)
    
    async def get_messages(self, 
                          start: int = 0, 
                          limit: int = 100,
                          filters: Dict = None) -> List[Message]:
        """Get messages with optional filtering"""
        query = filters or {}
        results = await self.db.find(
            query,
            skip=start,
            limit=limit
        )
        return [Message(**doc) for doc in results]
    
    def to_string(self) -> str:
        """Convert memory contents to string"""
        return "\n".join(m.content for m in self.messages)
    
    async def reset(self) -> None:
        """Clear all memory contents"""
        await self.db.delete_many({})
        self.messages = [] 