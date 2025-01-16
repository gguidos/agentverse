from typing import List, Dict
from pydantic import Field
from src.core.agentverse.memory.base import BaseMemory, Message
from src.core.agentverse.memory.registry import memory_registry

@memory_registry.register("chat_history")
class ChatHistoryMemory(BaseMemory):
    """Simple chat history memory that stores messages in order"""
    
    messages: List[Message] = Field(default_factory=list)
    
    async def add_message(self, messages: List[Message]) -> None:
        """Add messages to history"""
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
    
    def to_string(self, add_sender_prefix: bool = False) -> str:
        """Convert messages to string format"""
        if add_sender_prefix:
            return "\n".join(
                f"[{message.sender}]: {message.content}"
                if message.sender
                else message.content
                for message in self.messages
            )
        return "\n".join(m.content for m in self.messages)
    
    async def reset(self) -> None:
        """Clear chat history"""
        self.messages = [] 