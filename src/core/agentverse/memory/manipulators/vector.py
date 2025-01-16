from typing import Dict, Any, Optional, List, Union
import numpy as np
import logging

from src.core.agentverse.memory.manipulators.base import BaseManipulator
from src.core.agentverse.memory.types import MemoryData
from src.core.agentverse.exceptions import MemoryManipulationError

logger = logging.getLogger(__name__)

class VectorManipulator(BaseManipulator):
    """Vector data manipulator"""
    
    async def process_store(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> List[MemoryData]:
        """Process data for vector storage
        
        Args:
            data: Data to process
            
        Returns:
            Processed data
            
        Raises:
            MemoryManipulationError: If processing fails
        """
        try:
            # Convert single item to list
            if isinstance(data, dict):
                data = [data]
                
            # Process each item
            processed = []
            for item in data:
                # Extract content and metadata
                content = item.get("content")
                metadata = item.get("metadata", {})
                
                # Validate content
                if not content:
                    continue
                    
                # Create memory data
                memory_data = MemoryData(
                    content=content,
                    metadata=metadata
                )
                processed.append(memory_data)
                
            return processed
            
        except Exception as e:
            logger.error(f"Vector data processing failed: {str(e)}")
            raise MemoryManipulationError(f"Processing failed: {str(e)}")
    
    async def process_query(
        self,
        query: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process vector search query
        
        Args:
            query: Query to process
            
        Returns:
            Processed query
            
        Raises:
            MemoryManipulationError: If processing fails
        """
        try:
            # Handle string query
            if isinstance(query, str):
                return {
                    "content": query,
                    "metadata": {}
                }
                
            # Handle dict query
            if isinstance(query, dict):
                return {
                    "content": query.get("content", ""),
                    "metadata": query.get("metadata", {})
                }
                
            raise ValueError(f"Invalid query type: {type(query)}")
            
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            raise MemoryManipulationError(f"Query processing failed: {str(e)}")
    
    async def process_results(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process vector search results
        
        Args:
            results: Results to process
            
        Returns:
            Processed results
            
        Raises:
            MemoryManipulationError: If processing fails
        """
        try:
            processed = []
            for result in results:
                # Extract fields
                content = result.get("content")
                metadata = result.get("metadata", {})
                distance = result.get("distance")
                
                # Create processed result
                processed_result = {
                    "content": content,
                    "metadata": metadata
                }
                
                # Add distance if available
                if distance is not None:
                    processed_result["score"] = 1.0 - distance
                    
                processed.append(processed_result)
                
            return processed
            
        except Exception as e:
            logger.error(f"Results processing failed: {str(e)}")
            raise MemoryManipulationError(f"Results processing failed: {str(e)}")
    
    async def _validate_vector(
        self,
        vector: Union[List[float], np.ndarray]
    ) -> None:
        """Validate vector data
        
        Args:
            vector: Vector to validate
            
        Raises:
            ValueError: If vector is invalid
        """
        try:
            # Convert to numpy array
            if isinstance(vector, list):
                vector = np.array(vector)
                
            # Check dimensions
            if len(vector.shape) != 1:
                raise ValueError(f"Invalid vector shape: {vector.shape}")
                
            # Check for NaN/Inf
            if not np.all(np.isfinite(vector)):
                raise ValueError("Vector contains NaN or Inf values")
                
        except Exception as e:
            raise ValueError(f"Vector validation failed: {str(e)}") 