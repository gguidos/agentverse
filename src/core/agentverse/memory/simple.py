"""
Simple in-memory storage implementation
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from src.core.agentverse.message import Message
from src.core.agentverse.memory.base import BaseMemory
from src.core.agentverse.exceptions import MemoryError

class SimpleMemory(BaseMemory):
    """Simple in-memory storage"""
    
    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
    
    async def store(
        self,
        message: Message,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store message"""
        if not await self.validate_message(message):
            raise MemoryError("Invalid message")
            
        self.messages.append({
            "message": message,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow()
        })
    
    async def retrieve(
        self,
        query: str,
        k: int = 5
    ) -> List[Message]:
        """Simple keyword search"""
        matches = []
        for item in self.messages:
            if query.lower() in item["message"].content.lower():
                matches.append(item["message"])
                if len(matches) >= k:
                    break
        return matches
    
    async def clear(self) -> None:
        """Clear messages"""
        self.messages.clear()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        stats = await super().get_stats()
        stats.update({
            "message_count": len(self.messages),
            "last_message": self.messages[-1]["timestamp"] if self.messages else None
        })
        return stats 