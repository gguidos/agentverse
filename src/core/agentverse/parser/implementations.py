from typing import Dict, Any, Optional, ClassVar, List, Type
import logging
import json
import yaml
from datetime import datetime
from jsonschema import validate, ValidationError

from src.core.agentverse.parser.base import (
    BaseParser,
    ParseResult,
    ParserConfig,
    ParserError
)
from src.core.agentverse.parser.registry import parser_registry
from src.core.agentverse.llm.base import LLMResult

logger = logging.getLogger(__name__)

class JSONParserConfig(ParserConfig):
    """Configuration for JSON parser"""
    allow_empty_object: bool = False
    allow_arrays: bool = True
    max_depth: int = 10
    strict_schema: bool = True
    auto_fix: bool = True

class ChatParserConfig(ParserConfig):
    """Configuration for chat parser"""
    default_role: str = "assistant"
    include_metadata: bool = True
    track_tokens: bool = True
    normalize_content: bool = True

@parser_registry.register("json")
class JSONParser(BaseParser):
    """Parser for JSON formatted outputs"""
    
    name: ClassVar[str] = "json"
    description: ClassVar[str] = "Parser for JSON formatted outputs with schema validation"
    version: ClassVar[str] = "1.1.0"
    supported_formats: ClassVar[list] = ["json", "dict"]
    
    def __init__(
        self,
        schema: Optional[Dict] = None,
        config: Optional[JSONParserConfig] = None
    ):
        super().__init__(config=config or JSONParserConfig())
        self.schema = schema
    
    async def parse(self, output: LLMResult) -> ParseResult:
        """Parse JSON output
        
        Args:
            output: LLM output to parse
            
        Returns:
            ParseResult: Parsed JSON result
            
        Raises:
            ParserError: If parsing fails
        """
        try:
            content = output.content
            if not isinstance(content, str):
                content = str(content)
            
            # Parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                if self.config.auto_fix:
                    # Try to fix common JSON errors
                    content = self._fix_json(content)
                    data = json.loads(content)
                else:
                    raise ParserError("Invalid JSON format", content, {"error": str(e)})
            
            # Validate structure
            if not data and not self.config.allow_empty_object:
                raise ValueError("Empty JSON object not allowed")
            
            if isinstance(data, list) and not self.config.allow_arrays:
                raise ValueError("JSON arrays not allowed")
            
            # Validate against schema if provided
            if self.schema and self.config.strict_schema:
                try:
                    validate(instance=data, schema=self.schema)
                except ValidationError as e:
                    raise ParserError("Schema validation failed", content, {"error": str(e)})
            
            # Extract response field or use full data
            response = data.get("response", data)
            
            return ParseResult(
                content=response,
                type="json",
                format="object" if isinstance(data, dict) else "array",
                valid=True,
                metadata={
                    "raw_content": content,
                    "schema_valid": bool(self.schema),
                    "data_type": type(data).__name__,
                    "timestamp": datetime.utcnow()
                }
            )
            
        except Exception as e:
            logger.error(f"JSON parsing failed: {str(e)}")
            raise ParserError(str(e), content, {
                "parser": self.name,
                "version": self.version
            })
    
    def _fix_json(self, content: str) -> str:
        """Attempt to fix common JSON errors"""
        # Replace single quotes with double quotes
        content = content.replace("'", '"')
        
        # Add missing quotes around keys
        import re
        content = re.sub(r'(\w+):', r'"\1":', content)
        
        # Fix trailing commas
        content = re.sub(r',\s*([\]}])', r'\1', content)
        
        return content
    
    def _strict_validate(self, output: str) -> None:
        """Perform strict JSON validation"""
        try:
            data = json.loads(output)
            
            # Check depth
            def check_depth(obj, current_depth=0):
                if current_depth > self.config.max_depth:
                    raise ValueError(f"JSON exceeds maximum depth of {self.config.max_depth}")
                if isinstance(obj, dict):
                    for value in obj.values():
                        check_depth(value, current_depth + 1)
                elif isinstance(obj, list):
                    for item in obj:
                        check_depth(item, current_depth + 1)
            
            check_depth(data)
            
            # Validate against schema
            if self.schema:
                validate(instance=data, schema=self.schema)
                
        except Exception as e:
            raise ValueError(f"JSON validation failed: {str(e)}")

@parser_registry.register("chat")
class ChatParser(BaseParser):
    """Parser for chat message outputs"""
    
    name: ClassVar[str] = "chat"
    description: ClassVar[str] = "Parser for chat message outputs with metadata"
    version: ClassVar[str] = "1.1.0"
    supported_formats: ClassVar[list] = ["chat", "message"]
    
    def __init__(self, config: Optional[ChatParserConfig] = None):
        super().__init__(config=config or ChatParserConfig())
    
    async def parse(self, output: LLMResult) -> ParseResult:
        """Parse chat output
        
        Args:
            output: LLM output to parse
            
        Returns:
            ParseResult: Parsed chat result
            
        Raises:
            ParserError: If parsing fails
        """
        try:
            content = output.content
            if not isinstance(content, str):
                content = str(content)
            
            # Normalize content if enabled
            if self.config.normalize_content:
                content = self._normalize_chat_content(content)
            
            # Build metadata
            metadata = {
                "role": self.config.default_role,
                "timestamp": datetime.utcnow()
            }
            
            if self.config.track_tokens and hasattr(output, 'total_tokens'):
                metadata["tokens"] = output.total_tokens
            
            if self.config.include_metadata:
                metadata.update({
                    "raw_content": content,
                    "length": len(content)
                })
            
            return ParseResult(
                content=content,
                type="chat",
                format="message",
                valid=True,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Chat parsing failed: {str(e)}")
            raise ParserError(str(e), content, {
                "parser": self.name,
                "version": self.version
            })
    
    def _normalize_chat_content(self, content: str) -> str:
        """Normalize chat message content"""
        # Remove system markers
        content = content.replace("[SYSTEM]", "").replace("[/SYSTEM]", "")
        
        # Clean up whitespace
        content = " ".join(content.split())
        
        # Remove common prefixes
        prefixes = ["Assistant:", "AI:", "Bot:"]
        for prefix in prefixes:
            if content.startswith(prefix):
                content = content[len(prefix):].strip()
        
        return content
    
    def _strict_validate(self, output: str) -> None:
        """Perform strict chat message validation"""
        if not output:
            raise ValueError("Empty chat message")
        
        # Check for common issues
        if len(output.split()) < 2:
            raise ValueError("Message too short")
        
        if output.count('\n') > 10:
            raise ValueError("Too many line breaks")
        
        # Check for incomplete sentences
        if not output.rstrip('.')[-1] in '.!?':
            raise ValueError("Message ends without proper punctuation") 