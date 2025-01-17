from typing import Dict, Any, Optional, List, Union
import logging

from src.core.agentverse.memory import BaseMemory
from src.core.agentverse.message import Message

logger = logging.getLogger(__name__)

class MemoryHandlerMixin:
    """Mixin for memory handling capabilities"""
    
    def __init__(self, memory: Optional[BaseMemory] = None):
        """Initialize memory handler
        
        Args:
            memory: Optional memory backend
        """
        self.memory = memory
        self._context: List[Dict[str, Any]] = []
    
    async def remember(
        self,
        message: Union[Message, Dict[str, Any]],
        **kwargs
    ) -> None:
        """Store message in memory
        
        Args:
            message: Message to store
            **kwargs: Additional storage options
        """
        if not self.memory:
            return
            
        try:
            # Convert message to dict if needed
            if isinstance(message, Message):
                message = message.dict()
            
            # Store in memory
            await self.memory.store(
                data=message,
                **kwargs
            )
            
            # Update context
            self._context.append(message)
            
        except Exception as e:
            logger.error(f"Memory storage failed: {str(e)}")
    
    async def recall(
        self,
        query: Union[str, Dict[str, Any]],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Retrieve messages from memory
        
        Args:
            query: Search query
            **kwargs: Additional search options
            
        Returns:
            Retrieved messages
        """
        if not self.memory:
            return []
            
        try:
            # Search memory
            results = await self.memory.search(
                query=query,
                **kwargs
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Memory retrieval failed: {str(e)}")
            return []
    
    async def get_context(
        self,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get recent context
        
        Args:
            k: Number of messages
            filter_dict: Optional filter
            
        Returns:
            Recent messages
        """
        if not self.memory:
            return self._context[-k:]
            
        try:
            # Get recent messages
            results = await self.memory.search(
                query={
                    "sort": [{"timestamp": "desc"}],
                    "filter": filter_dict,
                    "limit": k
                }
            )
            
            return list(reversed(results))
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {str(e)}")
            return self._context[-k:]
    
    async def clear_context(self) -> None:
        """Clear memory context"""
        self._context.clear()
        
        if self.memory:
            try:
                await self.memory.clear()
            except Exception as e:
                logger.error(f"Memory clear failed: {str(e)}") 