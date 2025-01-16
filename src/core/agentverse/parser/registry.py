"""
Parser registry
"""

import logging
from typing import Dict, Type, Callable, Any
from functools import wraps

from src.core.agentverse.parser.base import BaseParser
from src.core.agentverse.exceptions import RegistrationError

logger = logging.getLogger(__name__)

class ParserRegistry:
    """Registry for parser implementations"""
    
    def __init__(self):
        self._parsers: Dict[str, Type[BaseParser]] = {}
    
    def register(self, name: str) -> Callable:
        """Register parser class
        
        Args:
            name: Parser name
            
        Returns:
            Registration decorator
        """
        def decorator(parser_class: Type[BaseParser]) -> Type[BaseParser]:
            if not issubclass(parser_class, BaseParser):
                raise RegistrationError(
                    message="Invalid parser class",
                    details={"class": parser_class.__name__}
                )
            
            self._parsers[name] = parser_class
            logger.info(f"Registered parser: {name}")
            return parser_class
            
        return decorator
    
    def get(self, name: str) -> Type[BaseParser]:
        """Get parser class by name
        
        Args:
            name: Parser name
            
        Returns:
            Parser class
            
        Raises:
            ComponentNotFoundError: If parser not found
        """
        if name not in self._parsers:
            raise ComponentNotFoundError(
                message=f"Parser not found: {name}"
            )
        return self._parsers[name]

# Global parser registry
parser_registry = ParserRegistry() 