from typing import Dict, Type, Any, Optional, List
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from src.core.agentverse.parser.base import BaseParser, ParserConfig

logger = logging.getLogger(__name__)

class ParserRegistryConfig(BaseModel):
    """Configuration for parser registry"""
    allow_duplicates: bool = False
    validate_parsers: bool = True
    track_usage: bool = True
    auto_initialize: bool = True

class ParserInfo(BaseModel):
    """Information about registered parser"""
    name: str
    description: str
    version: str
    supported_formats: List[str]
    config_class: Optional[Type[ParserConfig]] = None
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    usage_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ParserRegistry(BaseModel):
    """Registry for output parsers"""
    
    name: str = "ParserRegistry"
    config: ParserRegistryConfig = Field(default_factory=ParserRegistryConfig)
    entries: Dict[str, Type[BaseParser]] = Field(default_factory=dict)
    info: Dict[str, ParserInfo] = Field(default_factory=dict)
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
    def register(self, key: str, **metadata):
        """Register a parser class
        
        Args:
            key: Registry key for the parser
            **metadata: Additional metadata for the parser
        """
        def decorator(parser_class: Type[BaseParser]):
            # Validate parser class
            if not issubclass(parser_class, BaseParser):
                raise ValueError(f"Class {parser_class.__name__} must inherit from BaseParser")
            
            # Check for duplicates
            if key in self.entries and not self.config.allow_duplicates:
                raise KeyError(f"Parser '{key}' already registered")
            
            # Validate parser if enabled
            if self.config.validate_parsers:
                try:
                    if self.config.auto_initialize:
                        parser = parser_class()
                        # Test basic functionality
                        assert hasattr(parser, 'parse'), "Missing parse method"
                        assert hasattr(parser, '_strict_validate'), "Missing strict validation"
                except Exception as e:
                    logger.error(f"Parser validation failed: {str(e)}")
                    raise ValueError(f"Invalid parser class: {str(e)}")
            
            # Register parser
            self.entries[key] = parser_class
            
            # Store parser info
            self.info[key] = ParserInfo(
                name=getattr(parser_class, 'name', key),
                description=getattr(parser_class, 'description', ''),
                version=getattr(parser_class, 'version', '1.0.0'),
                supported_formats=getattr(parser_class, 'supported_formats', []),
                config_class=getattr(parser_class, 'config_class', None),
                metadata=metadata
            )
            
            logger.info(f"Registered parser '{key}' ({parser_class.__name__})")
            return parser_class
            
        return decorator
    
    def get(
        self,
        key: str,
        config: Optional[ParserConfig] = None,
        **kwargs
    ) -> BaseParser:
        """Get a parser instance
        
        Args:
            key: Registry key for the parser
            config: Optional parser configuration
            **kwargs: Additional arguments for parser initialization
        """
        if key not in self.entries:
            available = list(self.entries.keys())
            raise KeyError(f"Parser '{key}' not found. Available: {available}")
            
        try:
            parser_class = self.entries[key]
            
            # Update usage count
            if self.config.track_usage:
                self.info[key].usage_count += 1
            
            # Initialize with config if provided
            if config:
                return parser_class(config=config, **kwargs)
            return parser_class(**kwargs)
            
        except Exception as e:
            logger.error(f"Failed to instantiate parser '{key}': {str(e)}")
            raise
    
    def list_parsers(self) -> Dict[str, Dict[str, Any]]:
        """List all registered parsers with their info"""
        return {
            key: {
                "name": info.name,
                "description": info.description,
                "version": info.version,
                "supported_formats": info.supported_formats,
                "registered_at": info.registered_at.isoformat(),
                "usage_count": info.usage_count,
                "metadata": info.metadata
            }
            for key, info in self.info.items()
        }
    
    def get_parser_info(self, key: str) -> ParserInfo:
        """Get detailed information about a registered parser"""
        if key not in self.info:
            raise KeyError(f"Parser '{key}' not found")
        return self.info[key]
    
    def get_parsers_by_format(self, format: str) -> List[str]:
        """Get parsers that support a specific format"""
        return [
            key for key, info in self.info.items()
            if format in info.supported_formats
        ]
    
    def unregister(self, key: str) -> None:
        """Unregister a parser"""
        if key in self.entries:
            del self.entries[key]
            del self.info[key]
            logger.info(f"Unregistered parser '{key}'")
    
    def clear(self) -> None:
        """Clear all registered parsers"""
        self.entries.clear()
        self.info.clear()
        logger.info("Cleared parser registry")
    
    def get_most_used(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most frequently used parsers"""
        sorted_parsers = sorted(
            self.info.items(),
            key=lambda x: x[1].usage_count,
            reverse=True
        )
        
        return [{
            "key": key,
            "name": info.name,
            "usage_count": info.usage_count,
            "version": info.version,
            "formats": info.supported_formats
        } for key, info in sorted_parsers[:limit]]

# Create singleton instance
parser_registry = ParserRegistry()

# Example usage:
"""
@parser_registry.register("json", category="structured")
class JSONParser(BaseParser):
    name = "json"
    version = "1.1.0"
    supported_formats = ["json", "dict"]
    # ...

# Get parser instance
parser = parser_registry.get(
    "json",
    config=JSONParserConfig(strict_schema=True),
    schema=my_schema
)

# List available parsers
available = parser_registry.list_parsers()
""" 