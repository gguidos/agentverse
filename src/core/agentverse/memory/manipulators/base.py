"""Base memory manipulator module"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field

from src.core.agentverse.exceptions import MemoryManipulationError

if TYPE_CHECKING:
    from src.core.agentverse.agents.base_agent import BaseAgent
    from src.core.agentverse.memory import BaseMemory

class ManipulatorConfig(BaseModel):
    """Base configuration for memory manipulators"""
    name: str = "base"
    enabled: bool = True
    context_size: int = 5
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseMemoryManipulator(ABC):
    """Base class for memory manipulators"""
    
    def __init__(self, config: Optional[ManipulatorConfig] = None):
        self.agent: Optional['BaseAgent'] = None
        self.memory: Optional['BaseMemory'] = None
        self.config = config or ManipulatorConfig()
    
    @abstractmethod
    async def manipulate_memory(self, **kwargs) -> Dict[str, Any]:
        """Manipulate memory content
        
        Args:
            **kwargs: Additional manipulation options
            
        Returns:
            Manipulated memory data
            
        Raises:
            MemoryManipulationError: If manipulation fails
        """
        raise NotImplementedError
    
    def reset(self) -> None:
        """Reset manipulator state"""
        pass
    
    def validate_memory(self, data: Dict[str, Any]) -> bool:
        """Validate memory data
        
        Args:
            data: Memory data to validate
            
        Returns:
            Whether data is valid
        """
        return True
    
    async def get_context(
        self,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get memory context
        
        Args:
            k: Number of items
            filter_dict: Optional filter
            
        Returns:
            Context items
            
        Raises:
            MemoryManipulationError: If context retrieval fails
        """
        if not self.memory:
            raise MemoryManipulationError(
                message="Memory not initialized",
                details={"manipulator": self.__class__.__name__}
            )
            
        try:
            return await self.memory.search(
                query={
                    "sort": [{"timestamp": "desc"}],
                    "filter": filter_dict,
                    "limit": k
                }
            )
        except Exception as e:
            raise MemoryManipulationError(
                message="Failed to get context",
                details={
                    "error": str(e),
                    "k": k,
                    "filter": filter_dict
                }
            ) 