from typing import Dict, Any, Optional, List, Union
import logging

from src.core.agentverse.memory.types import MemoryConfig, MemoryData
from src.core.agentverse.exceptions import MemoryError

logger = logging.getLogger(__name__)

class BaseMemory:
    """Base memory class"""
    
    def __init__(
        self,
        backend: 'BaseBackend',  # Type hint with string to avoid circular import
        manipulator: 'BaseManipulator',  # Type hint with string to avoid circular import
        config: Optional[MemoryConfig] = None
    ):
        """Initialize memory
        
        Args:
            backend: Memory backend
            manipulator: Memory manipulator
            config: Optional memory configuration
        """
        self.backend = backend
        self.manipulator = manipulator
        self.config = config or MemoryConfig(
            backend_type="vector",
            backend_name="faiss"
        )
    
    async def store(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        **kwargs
    ) -> None:
        """Store data in memory
        
        Args:
            data: Data to store
            **kwargs: Additional storage options
            
        Raises:
            MemoryError: If storage fails
        """
        try:
            # Manipulate data
            processed_data = await self.manipulator.process_store(data)
            
            # Store in backend
            await self.backend.store(processed_data, **kwargs)
            
        except Exception as e:
            logger.error(f"Memory storage failed: {str(e)}")
            raise MemoryError(f"Storage failed: {str(e)}")
    
    async def retrieve(
        self,
        query: Union[str, Dict[str, Any]],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Retrieve data from memory
        
        Args:
            query: Search query
            **kwargs: Additional retrieval options
            
        Returns:
            Retrieved data
            
        Raises:
            MemoryError: If retrieval fails
        """
        try:
            # Process query
            processed_query = await self.manipulator.process_query(query)
            
            # Search backend
            results = await self.backend.search(processed_query, **kwargs)
            
            # Post-process results
            processed_results = await self.manipulator.process_results(results)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Memory retrieval failed: {str(e)}")
            raise MemoryError(f"Retrieval failed: {str(e)}")
    
    async def clear(self, **kwargs) -> None:
        """Clear memory
        
        Args:
            **kwargs: Additional clear options
            
        Raises:
            MemoryError: If clear fails
        """
        try:
            await self.backend.clear(**kwargs)
            
        except Exception as e:
            logger.error(f"Memory clear failed: {str(e)}")
            raise MemoryError(f"Clear failed: {str(e)}")
    
    async def _validate_data(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> None:
        """Validate input data
        
        Args:
            data: Data to validate
            
        Raises:
            ValueError: If data is invalid
        """
        if isinstance(data, list):
            if not all(isinstance(d, dict) for d in data):
                raise ValueError("List items must be dictionaries")
        elif not isinstance(data, dict):
            raise ValueError("Data must be dictionary or list of dictionaries")
    
    async def _check_size_limit(self) -> None:
        """Check memory size limit
        
        Raises:
            MemoryError: If size limit exceeded
        """
        if self.config.max_size:
            # Implement size checking
            pass 