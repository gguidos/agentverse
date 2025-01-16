from typing import Dict, Any, Optional, List, Union
from abc import ABC, abstractmethod
import logging

from src.core.agentverse.memory.types import MemoryData
from src.core.agentverse.exceptions import MemoryManipulationError

logger = logging.getLogger(__name__)

class BaseManipulator(ABC):
    """Base class for memory manipulators"""
    
    @abstractmethod
    async def process_store(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> List[MemoryData]:
        """Process data for storage
        
        Args:
            data: Data to process
            
        Returns:
            Processed data
            
        Raises:
            MemoryManipulationError: If processing fails
        """
        pass
    
    @abstractmethod
    async def process_query(
        self,
        query: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process search query
        
        Args:
            query: Query to process
            
        Returns:
            Processed query
            
        Raises:
            MemoryManipulationError: If processing fails
        """
        pass
    
    @abstractmethod
    async def process_results(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process search results
        
        Args:
            results: Results to process
            
        Returns:
            Processed results
            
        Raises:
            MemoryManipulationError: If processing fails
        """
        pass 