"""Base Selector Module"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')  # Generic type for selected items

class SelectorConfig(BaseModel):
    """Selector configuration"""
    max_results: int = 10
    min_score: float = 0.0
    timeout: float = 5.0

class BaseSelector(ABC, Generic[T]):
    """Base class for selectors"""
    
    def __init__(self, config: Optional[SelectorConfig] = None):
        self.config = config or SelectorConfig()
    
    @abstractmethod
    async def select(
        self,
        candidates: List[T],
        **kwargs
    ) -> List[T]:
        """Select items from candidates
        
        Args:
            candidates: List of items to select from
            **kwargs: Selection criteria
            
        Returns:
            Selected items
        """
        pass
    
    @abstractmethod
    async def score(
        self,
        item: T,
        **kwargs
    ) -> float:
        """Score an item based on criteria
        
        Args:
            item: Item to score
            **kwargs: Scoring criteria
            
        Returns:
            Score between 0 and 1
        """
        pass 