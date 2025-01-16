from typing import Dict, Any, Optional, ClassVar
import logging
import json
from datetime import datetime

from src.core.agentverse.parser.base import (
    BaseParser,
    ParseResult,
    ParserConfig,
    ParserError
)
from src.core.agentverse.llm.base import LLMResult

logger = logging.getLogger(__name__)

class DefaultParserConfig(ParserConfig):
    """Configuration for default parser"""
    allow_empty: bool = False
    min_length: int = 1
    max_length: int = 100000
    strip_whitespace: bool = True
    normalize_newlines: bool = True
    remove_extra_spaces: bool = True

class DefaultParser(BaseParser):
    """Default implementation of output parser"""
    
    name: ClassVar[str] = "default"
    description: ClassVar[str] = "Default parser for text output"
    version: ClassVar[str] = "1.1.0"
    supported_formats: ClassVar[list] = ["text", "json", "yaml"]
    
    def __init__(self, config: Optional[DefaultParserConfig] = None):
        super().__init__(config=config or DefaultParserConfig())
    
    async def parse(self, output: LLMResult) -> ParseResult:
        """Parse LLM output into standard format
        
        Args:
            output: LLM output to parse
            
        Returns:
            ParseResult: Parsed output
            
        Raises:
            ParserError: If parsing fails
        """
        try:
            # Extract content
            content = output.content
            if not content:
                if not self.config.allow_empty:
                    raise ValueError("Empty output not allowed")
                content = ""
            
            # Convert to string if needed
            if not isinstance(content, str):
                content = str(content)
            
            # Apply text normalization if enabled
            if self.config.strip_whitespace:
                content = content.strip()
            if self.config.normalize_newlines:
                content = content.replace('\r\n', '\n').replace('\r', '\n')
            if self.config.remove_extra_spaces:
                content = ' '.join(content.split())
            
            # Validate length
            if len(content) < self.config.min_length:
                raise ValueError(f"Output too short (min {self.config.min_length} chars)")
            if len(content) > self.config.max_length:
                raise ValueError(f"Output too long (max {self.config.max_length} chars)")
            
            # Try to detect format
            format_type = self._detect_format(content)
            
            # Create result
            return ParseResult(
                content=content,
                type="text",
                format=format_type,
                valid=True,
                metadata={
                    "raw_output": output.dict(),
                    "timestamp": output.timestamp.isoformat() if hasattr(output, 'timestamp') else datetime.utcnow().isoformat(),
                    "length": len(content),
                    "format_type": format_type,
                    "normalized": self.config.strip_whitespace or self.config.normalize_newlines
                }
            )
            
        except Exception as e:
            logger.error(f"Parsing failed: {str(e)}")
            raise ParserError(
                message=str(e),
                output=output.content if isinstance(output.content, str) else None,
                details={
                    "parser": self.name,
                    "version": self.version,
                    "config": self.config.dict()
                }
            )
    
    def _detect_format(self, content: str) -> str:
        """Detect content format
        
        Args:
            content: Content to analyze
            
        Returns:
            str: Detected format type
        """
        # Try JSON
        if content.strip().startswith('{') or content.strip().startswith('['):
            try:
                json.loads(content)
                return "json"
            except:
                pass
        
        # Try YAML
        if ':' in content and '\n' in content:
            try:
                import yaml
                yaml.safe_load(content)
                return "yaml"
            except:
                pass
        
        return "text"
    
    def _strict_validate(self, output: str) -> None:
        """Perform strict output validation
        
        Args:
            output: Output to validate
            
        Raises:
            ValueError: If validation fails
        """
        if not output:
            raise ValueError("Empty output")
            
        if len(output) < self.config.min_length:
            raise ValueError(f"Output too short (min {self.config.min_length} chars)")
            
        if len(output) > self.config.max_length:
            raise ValueError(f"Output too long (max {self.config.max_length} chars)")
            
        # Additional format-specific validation
        format_type = self._detect_format(output)
        if format_type == "json":
            try:
                json.loads(output)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {str(e)}")
        elif format_type == "yaml":
            try:
                import yaml
                yaml.safe_load(output)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML format: {str(e)}")
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text content
        
        Args:
            text: Text to normalize
            
        Returns:
            str: Normalized text
        """
        if self.config.strip_whitespace:
            text = text.strip()
        if self.config.normalize_newlines:
            text = text.replace('\r\n', '\n').replace('\r', '\n')
        if self.config.remove_extra_spaces:
            text = ' '.join(text.split())
        return text 