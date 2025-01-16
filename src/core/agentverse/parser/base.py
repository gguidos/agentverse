from abc import ABC, abstractmethod
from typing import NamedTuple, Any, Dict, Optional, List, ClassVar, Type
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import json

from src.core.agentverse.llm.base import LLMResult

logger = logging.getLogger(__name__)

class ParserError(Exception):
    """Error when parsing model output"""
    def __init__(
        self,
        message: str,
        output: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.output = output
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        
        super().__init__(
            f"Parser error: {message}\n"
            f"Output: {output}\n"
            f"Details: {json.dumps(details, indent=2) if details else 'None'}"
        )

class ParseResult(BaseModel):
    """Structured parse result"""
    content: Any
    type: str
    format: str
    valid: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

class ParserConfig(BaseModel):
    """Configuration for parsers"""
    strict_mode: bool = True
    max_retries: int = 3
    timeout: float = 30.0
    cache_results: bool = True
    validate_output: bool = True
    
    model_config = {
        "extra": "allow"
    }

class BaseParser(ABC, BaseModel):
    """Base class for output parsers"""
    
    name: ClassVar[str] = "base_parser"
    description: ClassVar[str] = "Base parser class"
    version: ClassVar[str] = "1.0.0"
    supported_formats: ClassVar[List[str]] = ["text"]
    
    config: ParserConfig = Field(default_factory=ParserConfig)
    _cache: Dict[str, ParseResult] = {}
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
    @abstractmethod
    async def parse(self, output: LLMResult) -> ParseResult:
        """Parse LLM output into structured format
        
        Args:
            output: LLM output to parse
            
        Returns:
            ParseResult: Structured parse result
            
        Raises:
            ParserError: If parsing fails
        """
        pass
    
    def _validate_output(self, output: str) -> bool:
        """Validate output format
        
        Args:
            output: Output string to validate
            
        Returns:
            bool: Whether output is valid
        """
        if not output or not isinstance(output, str):
            return False
            
        if self.config.strict_mode:
            try:
                self._strict_validate(output)
            except Exception as e:
                logger.warning(f"Strict validation failed: {str(e)}")
                return False
                
        return True
    
    @abstractmethod
    def _strict_validate(self, output: str) -> None:
        """Perform strict output validation
        
        Args:
            output: Output string to validate
            
        Raises:
            ValueError: If validation fails
        """
        pass
    
    def _get_cache_key(self, output: str) -> str:
        """Generate cache key for output
        
        Args:
            output: Output string
            
        Returns:
            str: Cache key
        """
        return hashlib.md5(output.encode()).hexdigest()
    
    def _cache_result(self, output: str, result: ParseResult) -> None:
        """Cache parse result
        
        Args:
            output: Original output string
            result: Parse result to cache
        """
        if self.config.cache_results:
            key = self._get_cache_key(output)
            self._cache[key] = result
    
    def _get_cached_result(self, output: str) -> Optional[ParseResult]:
        """Get cached parse result
        
        Args:
            output: Original output string
            
        Returns:
            Optional[ParseResult]: Cached result if found
        """
        if self.config.cache_results:
            key = self._get_cache_key(output)
            return self._cache.get(key)
        return None
    
    def clear_cache(self) -> None:
        """Clear parser cache"""
        self._cache.clear()
        logger.info(f"Cleared cache for {self.name} parser")
    
    async def safe_parse(
        self,
        output: LLMResult,
        retry_count: int = 0
    ) -> ParseResult:
        """Safely parse output with retries
        
        Args:
            output: LLM output to parse
            retry_count: Current retry attempt
            
        Returns:
            ParseResult: Parse result
            
        Raises:
            ParserError: If parsing fails after retries
        """
        try:
            # Check cache first
            if isinstance(output.content, str):
                cached = self._get_cached_result(output.content)
                if cached:
                    return cached
            
            # Validate if enabled
            if (
                self.config.validate_output and
                isinstance(output.content, str) and
                not self._validate_output(output.content)
            ):
                raise ValueError("Invalid output format")
            
            # Parse output
            result = await self.parse(output)
            
            # Cache result
            if isinstance(output.content, str):
                self._cache_result(output.content, result)
            
            return result
            
        except Exception as e:
            if retry_count < self.config.max_retries:
                logger.warning(f"Parse attempt {retry_count + 1} failed: {str(e)}")
                return await self.safe_parse(output, retry_count + 1)
            else:
                logger.error(f"Parsing failed after {retry_count} retries: {str(e)}")
                raise ParserError(
                    message=str(e),
                    output=output.content if isinstance(output.content, str) else None,
                    details={
                        "parser": self.name,
                        "version": self.version,
                        "retries": retry_count
                    }
                )
    
    def __repr__(self) -> str:
        return f"{self.name}Parser(version={self.version})"
    
    def __str__(self) -> str:
        return self.__repr__() 