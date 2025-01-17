"""Filter memory manipulator implementation"""

from typing import Dict, Any, Optional, List
import logging
from pydantic import Field

from src.core.agentverse.memory.manipulators.base import (
    BaseMemoryManipulator,
    ManipulatorConfig
)
from src.core.agentverse.exceptions import MemoryManipulationError

logger = logging.getLogger(__name__)

class FilterConfig(ManipulatorConfig):
    """Configuration for filter manipulator"""
    name: str = "filter"
    filters: Dict[str, Any] = Field(default_factory=dict)
    exclude_types: List[str] = Field(default_factory=list)
    include_types: List[str] = Field(default_factory=list)

class FilterMemoryManipulator(BaseMemoryManipulator):
    """Memory manipulator that filters context based on rules"""
    
    def __init__(self, config: Optional[FilterConfig] = None):
        super().__init__(config or FilterConfig())
        self.config: FilterConfig = self.config  # Type hint
    
    async def manipulate_memory(self, **kwargs) -> Dict[str, Any]:
        """Filter memory content
        
        Args:
            **kwargs: Additional manipulation options
                - filters: Additional filters to apply
                - exclude_types: Message types to exclude
                - include_types: Message types to include
                
        Returns:
            Filtered memory data
            
        Raises:
            MemoryManipulationError: If manipulation fails
        """
        try:
            # Merge config filters with kwargs
            filters = {
                **self.config.filters,
                **kwargs.get("filters", {})
            }
            
            exclude_types = list(set(
                self.config.exclude_types + 
                kwargs.get("exclude_types", [])
            ))
            
            include_types = list(set(
                self.config.include_types +
                kwargs.get("include_types", [])
            ))
            
            # Get context with filters
            context = await self.get_context(
                k=kwargs.get("context_size", self.config.context_size),
                filter_dict=filters
            )
            
            # Apply type filters
            filtered_context = [
                item for item in context
                if (
                    isinstance(item, dict) and
                    (not include_types or item.get("type") in include_types) and
                    item.get("type") not in exclude_types
                )
            ]
            
            # Concatenate filtered content
            content = "\n".join([
                item.get("content", "")
                for item in filtered_context
            ])
            
            return {
                "content": content,
                "context": filtered_context,
                "metadata": {
                    "manipulator": self.__class__.__name__,
                    "context_size": len(filtered_context),
                    "filters": filters,
                    "exclude_types": exclude_types,
                    "include_types": include_types,
                    "empty": not filtered_context
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