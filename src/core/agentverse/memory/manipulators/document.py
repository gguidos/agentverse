from typing import Dict, Any, Optional, List, Union
import logging
import json

from src.core.agentverse.memory.manipulators.base import BaseManipulator
from src.core.agentverse.memory.types import MemoryData
from src.core.agentverse.exceptions import MemoryManipulationError

logger = logging.getLogger(__name__)

class DocumentManipulator(BaseManipulator):
    """Document data manipulator"""
    
    async def process_store(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> List[MemoryData]:
        """Process data for document storage
        
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
                    
                # Process content based on type
                if isinstance(content, (dict, list)):
                    content = json.dumps(content)
                elif not isinstance(content, str):
                    content = str(content)
                
                # Add content type to metadata
                metadata["content_type"] = type(item.get("content")).__name__
                
                # Create memory data
                memory_data = MemoryData(
                    content=content,
                    metadata=metadata
                )
                processed.append(memory_data)
                
            return processed
            
        except Exception as e:
            logger.error(f"Document data processing failed: {str(e)}")
            raise MemoryManipulationError(f"Processing failed: {str(e)}")
    
    async def process_query(
        self,
        query: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process document search query
        
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
                content = query.get("content", "")
                metadata = query.get("metadata", {})
                
                # Process content if needed
                if isinstance(content, (dict, list)):
                    content = json.dumps(content)
                elif not isinstance(content, str):
                    content = str(content)
                    
                return {
                    "content": content,
                    "metadata": metadata
                }
                
            raise ValueError(f"Invalid query type: {type(query)}")
            
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            raise MemoryManipulationError(f"Query processing failed: {str(e)}")
    
    async def process_results(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Process document search results
        
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
                score = result.get("score", 0.0)
                
                # Convert content back to original type
                content_type = metadata.get("content_type")
                if content_type:
                    try:
                        if content_type in ("dict", "list"):
                            content = json.loads(content)
                        elif content_type != "str":
                            # Try to convert to original type
                            content = eval(f"{content_type}({content})")
                    except:
                        # Keep as string if conversion fails
                        pass
                
                # Create processed result
                processed_result = {
                    "content": content,
                    "metadata": metadata,
                    "score": score
                }
                processed.append(processed_result)
                
            return processed
            
        except Exception as e:
            logger.error(f"Results processing failed: {str(e)}")
            raise MemoryManipulationError(f"Results processing failed: {str(e)}")
    
    async def _validate_document(
        self,
        content: Any,
        metadata: Dict[str, Any]
    ) -> None:
        """Validate document data
        
        Args:
            content: Document content
            metadata: Document metadata
            
        Raises:
            ValueError: If document is invalid
        """
        # Validate content
        if content is None:
            raise ValueError("Empty document content")
            
        # Validate metadata
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")
            
        # Check required metadata fields
        required_fields = ["content_type"]
        missing_fields = [f for f in required_fields if f not in metadata]
        if missing_fields:
            raise ValueError(f"Missing required metadata fields: {missing_fields}") 