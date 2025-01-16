from typing import List, Dict
from src.core.agentverse.memory.base import BaseMemory, Message
from src.core.agentverse.memory.registry import memory_registry

@memory_registry.register("simple")
class SimpleMemory(BaseMemory):
    """Simple in-memory storage"""
    
    async def add_message(self, messages: List[Message]) -> None:
        """Add messages to memory"""
        self.messages.extend(messages)
    
    async def get_messages(self, 
                          start: int = 0,
                          limit: int = 100,
                          filters: Dict = None) -> List[Message]:
        """Get messages with optional filtering"""
        filtered = self.messages
        if filters:
            filtered = [
                m for m in filtered 
                if all(m.dict().get(k) == v for k, v in filters.items())
            ]
        return filtered[start:start+limit]
    
    def to_string(self) -> str:
        """Convert memory contents to string"""
        return "\n".join(m.content for m in self.messages)
    
    async def reset(self) -> None:
        """Clear all memory contents"""
        self.messages = [] 