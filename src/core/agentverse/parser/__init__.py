"""
AgentVerse Parser Module

This module provides parsers for structured data formats.
"""

from src.core.agentverse.parser.base import BaseParser, ParserConfig
from src.core.agentverse.parser.implementations import JSONParser
from src.core.agentverse.parser.registry import parser_registry

# Register built-in parsers
parser_registry.register("json")(JSONParser)

__all__ = [
    # Base classes
    "BaseParser",
    "ParserConfig",
    
    # Implementations
    "JSONParser",
    
    # Registry
    "parser_registry"
] 