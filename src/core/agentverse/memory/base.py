"""
Base memory interface
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

from src.core.agentverse.message import Message
from src.core.agentverse.exceptions import MemoryError

class BaseMemory(ABC):
    """Abstract base class for memory implementations"""
    
    @abstractmethod
    async def store(
        self,
        message: Message,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store message in memory
        
        Args:
            message: Message to store
            metadata: Optional metadata
            
        Raises:
            MemoryError: If storage fails
        """
        pass
    
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        k: int = 5
    ) -> List[Message]:
        """Retrieve messages from memory
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of matching messages
            
        Raises:
            MemoryError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all messages from memory
        
        Raises:
            MemoryError: If clear fails
        """
        pass
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics
        
        Returns:
            Dictionary of statistics
        """
        return {
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def validate_message(self, message: Message) -> bool:
        """Validate message before storage
        
        Args:
            message: Message to validate
            
        Returns:
            Whether message is valid
        """
        return bool(message.content and message.type and message.role) 