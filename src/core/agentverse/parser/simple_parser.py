from typing import Dict, Any, Optional, ClassVar
import logging
from datetime import datetime

from src.core.agentverse.parser.base import (
    BaseParser,
    ParseResult,
    ParserConfig,
    ParserError
)
from src.core.agentverse.llm.base import LLMResult

logger = logging.getLogger(__name__)

class SimpleParserConfig(ParserConfig):
    """Configuration for simple parser"""
    strip_whitespace: bool = True
    normalize_newlines: bool = True
    min_length: int = 0
    max_length: int = 100000
    allow_empty: bool = True

class SimpleParser(BaseParser):
    """Simple parser that returns minimally processed text"""
    
    name: ClassVar[str] = "simple"
    description: ClassVar[str] = "Basic parser for raw text output with minimal processing"
    version: ClassVar[str] = "1.1.0"
    supported_formats: ClassVar[list] = ["text", "raw"]
    
    def __init__(self, config: Optional[SimpleParserConfig] = None):
        super().__init__(config=config or SimpleParserConfig())
    
    async def parse(self, output: LLMResult) -> ParseResult:
        """Parse raw output with minimal processing
        
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
            if not isinstance(content, str):
                content = str(content)
            
            # Apply basic normalization if enabled
            if self.config.strip_whitespace:
                content = content.strip()
            if self.config.normalize_newlines:
                content = content.replace('\r\n', '\n').replace('\r', '\n')
            
            # Validate length
            if not content and not self.config.allow_empty:
                raise ValueError("Empty content not allowed")
            if len(content) < self.config.min_length:
                raise ValueError(f"Content too short (min {self.config.min_length} chars)")
            if len(content) > self.config.max_length:
                raise ValueError(f"Content too long (max {self.config.max_length} chars)")
            
            # Create result
            return ParseResult(
                content=content,
                type="text",
                format="raw",
                valid=True,
                metadata={
                    "length": len(content),
                    "timestamp": datetime.utcnow(),
                    "normalized": self.config.strip_whitespace or self.config.normalize_newlines,
                    "lines": content.count('\n') + 1 if content else 0,
                    "words": len(content.split()) if content else 0
                }
            )
            
        except Exception as e:
            logger.error(f"Simple parsing failed: {str(e)}")
            raise ParserError(
                message=str(e),
                output=output.content if isinstance(output.content, str) else None,
                details={
                    "parser": self.name,
                    "version": self.version,
                    "config": self.config.dict()
                }
            )
    
    def _strict_validate(self, output: str) -> None:
        """Perform strict validation of output
        
        Args:
            output: Output to validate
            
        Raises:
            ValueError: If validation fails
        """
        if not output and not self.config.allow_empty:
            raise ValueError("Empty output not allowed")
        
        if len(output) < self.config.min_length:
            raise ValueError(f"Output too short (min {self.config.min_length} chars)")
        
        if len(output) > self.config.max_length:
            raise ValueError(f"Output too long (max {self.config.max_length} chars)")
        
        # Check for basic text validity
        try:
            output.encode('utf-8').decode('utf-8')
        except UnicodeError:
            raise ValueError("Invalid UTF-8 encoding")
    
    def _get_text_stats(self, text: str) -> Dict[str, int]:
        """Get basic text statistics
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with text statistics
        """
        return {
            "length": len(text),
            "lines": text.count('\n') + 1,
            "words": len(text.split()),
            "chars_per_line": len(text) // (text.count('\n') + 1) if text else 0,
            "words_per_line": len(text.split()) // (text.count('\n') + 1) if text else 0
        } 