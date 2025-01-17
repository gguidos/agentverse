"""Summarize memory manipulator implementation"""

from typing import Dict, Any, Optional, List
import logging

from src.core.agentverse.memory.manipulators.base import BaseMemoryManipulator
from src.core.agentverse.exceptions import MemoryManipulationError

logger = logging.getLogger(__name__)

class SummarizeMemoryManipulator(BaseMemoryManipulator):
    """Memory manipulator that summarizes context"""
    
    async def manipulate_memory(self, **kwargs) -> Dict[str, Any]:
        """Summarize memory content
        
        Args:
            **kwargs: Additional manipulation options
                - max_length: Maximum summary length
                - min_length: Minimum summary length
                - context_size: Number of context items
                
        Returns:
            Manipulated memory data with summary
            
        Raises:
            MemoryManipulationError: If manipulation fails
        """
        try:
            # Get recent context
            context = await self.get_context(
                k=kwargs.get("context_size", 10),
                filter_dict=kwargs.get("filter_dict")
            )
            
            # Basic validation
            if not context:
                return {
                    "content": "",
                    "context": [],
                    "summary": "",
                    "metadata": {
                        "manipulator": self.__class__.__name__,
                        "empty": True
                    }
                }
            
            # Concatenate context
            content = "\n".join([
                item.get("content", "") 
                for item in context
                if isinstance(item, dict)
            ])
            
            # Generate summary if LLM available
            summary = ""
            if self.agent and self.agent.llm:
                try:
                    prompt = (
                        f"Please summarize the following conversation in "
                        f"{kwargs.get('max_length', 200)} characters or less:\n\n"
                        f"{content}"
                    )
                    summary = await self.agent.llm.generate(prompt)
                except Exception as e:
                    logger.warning(f"Summary generation failed: {str(e)}")
                    summary = content[:kwargs.get("max_length", 200)] + "..."
            else:
                # Fallback to truncation
                summary = content[:kwargs.get("max_length", 200)] + "..."
            
            return {
                "content": content,
                "context": context,
                "summary": summary,
                "metadata": {
                    "manipulator": self.__class__.__name__,
                    "context_size": len(context),
                    "summary_length": len(summary),
                    "empty": False,
                    "summarization_method": "llm" if (self.agent and self.agent.llm) else "truncation"
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
        required_fields = ["content", "context", "summary", "metadata"]
        return all(field in data for field in required_fields) 