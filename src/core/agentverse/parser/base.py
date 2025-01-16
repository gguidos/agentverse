"""
Base parser interface
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

class ParserConfig(BaseModel):
    """Base configuration for parsers"""
    schema: Optional[Dict[str, Any]] = None
    strict: bool = True
    max_depth: int = 10

class BaseParser(ABC):
    """Abstract base class for parsers"""
    
    def __init__(self, config: Optional[ParserConfig] = None):
        self.config = config or ParserConfig()
    
    @abstractmethod
    async def parse(self, content: str) -> Dict[str, Any]:
        """Parse content into structured data
        
        Args:
            content: Content to parse
            
        Returns:
            Parsed data structure
            
        Raises:
            ParserError: If parsing fails
        """
        pass
    
    @abstractmethod
    async def format(self, data: Dict[str, Any]) -> str:
        """Format data structure into string
        
        Args:
            data: Data to format
            
        Returns:
            Formatted string
            
        Raises:
            ParserError: If formatting fails
        """
        pass 