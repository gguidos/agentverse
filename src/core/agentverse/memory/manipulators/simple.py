"""Simple memory manipulator implementation"""

from typing import Dict, Any, Optional, List
import logging

from src.core.agentverse.memory.manipulators.base import BaseMemoryManipulator
from src.core.agentverse.exceptions import MemoryManipulationError

logger = logging.getLogger(__name__)

class SimpleMemoryManipulator(BaseMemoryManipulator):
    """Simple memory manipulator that passes through data with basic validation"""
    
    async def manipulate_memory(self, **kwargs) -> Dict[str, Any]:
        """Simple pass-through manipulation
        
        Args:
            **kwargs: Additional manipulation options
            
        Returns:
            Manipulated memory data
            
        Raises:
            MemoryManipulationError: If manipulation fails
        """
        try:
            # Get recent context
            context = await self.get_context(
                k=kwargs.get("context_size", 5),
                filter_dict=kwargs.get("filter_dict")
            )
            
            # Basic validation
            if not context:
                return {
                    "content": "",
                    "context": [],
                    "metadata": {
                        "manipulator": self.__class__.__name__,
                        "empty": True
                    }
                }
            
            # Simple concatenation of context
            content = "\n".join([
                item.get("content", "") 
                for item in context
                if isinstance(item, dict)
            ])
            
            return {
                "content": content,
                "context": context,
                "metadata": {
                    "manipulator": self.__class__.__name__,
                    "context_size": len(context),
                    "empty": False
                }
            }
            
        except Exception as e:
            logger.error(f"Memory manipulation failed: {str(e)}")
            raise MemoryManipulationError(
                message="Failed to manipulate memory",
                details={
                    "error": str(e),
                    "manipulator": self.__class__.__name__,
                    "kwargs": kwargs
                }
            )
    
    def validate_memory(self, data: Dict[str, Any]) -> bool:
        """Validate memory data
        
        Args:
            data: Memory data to validate
            
        Returns:
            Whether data is valid
        """
        # Basic validation
        if not isinstance(data, dict):
            return False
            
        # Check required fields
        required_fields = ["content", "context", "metadata"]
        return all(field in data for field in required_fields) 