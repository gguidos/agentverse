from typing import Dict, Any, Optional, ClassVar, List
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

class FormParserConfig(ParserConfig):
    """Configuration for form parser"""
    completion_keywords: List[str] = ["INTERVIEW_COMPLETE", "FORM_COMPLETE", "DONE"]
    extract_fields: bool = True
    validate_required: bool = True
    required_fields: List[str] = []
    field_separator: str = ":"
    normalize_fields: bool = True
    max_field_length: int = 1000

class FormParser(BaseParser):
    """Parser for form and interview responses"""
    
    name: ClassVar[str] = "form"
    description: ClassVar[str] = "Parser for structured form and interview responses"
    version: ClassVar[str] = "1.1.0"
    supported_formats: ClassVar[list] = ["form", "interview", "qa"]
    
    def __init__(self, config: Optional[FormParserConfig] = None):
        super().__init__(config=config or FormParserConfig())
    
    async def parse(self, output: LLMResult) -> ParseResult:
        """Parse form/interview output
        
        Args:
            output: LLM output to parse
            
        Returns:
            ParseResult: Parsed form result
            
        Raises:
            ParserError: If parsing fails
        """
        try:
            content = output.content
            if not isinstance(content, str):
                content = str(content)
            
            # Normalize content
            content = content.strip()
            
            # Check for completion
            if any(keyword.lower() in content.lower() 
                  for keyword in self.config.completion_keywords):
                return ParseResult(
                    content={
                        "status": "complete",
                        "next_question": None
                    },
                    type="form",
                    format="completion",
                    metadata={
                        "timestamp": datetime.utcnow(),
                        "raw_content": content
                    }
                )
            
            # Extract fields if enabled
            fields = {}
            if self.config.extract_fields:
                fields = self._extract_fields(content)
                
                # Validate required fields
                if self.config.validate_required:
                    missing = [
                        field for field in self.config.required_fields
                        if field not in fields
                    ]
                    if missing:
                        raise ValueError(f"Missing required fields: {', '.join(missing)}")
            
            # Determine if this is a question or response
            is_question = any(q in content.lower() 
                            for q in ["?", "please provide", "tell me"])
            
            result = {
                "status": "in_progress",
                "next_question": content if is_question else None,
                "response": None if is_question else content,
                "fields": fields
            }
            
            return ParseResult(
                content=result,
                type="form",
                format="question" if is_question else "response",
                metadata={
                    "timestamp": datetime.utcnow(),
                    "raw_content": content,
                    "field_count": len(fields),
                    "is_question": is_question
                }
            )
            
        except Exception as e:
            logger.error(f"Form parsing failed: {str(e)}")
            raise ParserError(
                message=str(e),
                output=output.content if isinstance(output.content, str) else None,
                details={
                    "parser": self.name,
                    "version": self.version,
                    "config": self.config.dict()
                }
            )
    
    def _extract_fields(self, content: str) -> Dict[str, str]:
        """Extract fields from form content
        
        Args:
            content: Form content to parse
            
        Returns:
            Dict mapping field names to values
        """
        fields = {}
        
        # Split into lines
        lines = content.split('\n')
        
        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue
                
            # Look for field separator
            if self.config.field_separator in line:
                field, value = line.split(self.config.field_separator, 1)
                
                # Clean up field name and value
                field = field.strip().lower()
                if self.config.normalize_fields:
                    field = field.replace(' ', '_')
                value = value.strip()
                
                # Validate field length
                if len(value) > self.config.max_field_length:
                    logger.warning(
                        f"Field '{field}' exceeds max length "
                        f"({len(value)} > {self.config.max_field_length})"
                    )
                    value = value[:self.config.max_field_length]
                
                fields[field] = value
        
        return fields
    
    def _strict_validate(self, output: str) -> None:
        """Perform strict validation of form output
        
        Args:
            output: Output to validate
            
        Raises:
            ValueError: If validation fails
        """
        if not output:
            raise ValueError("Empty form output")
        
        # Check for completion keywords
        is_complete = any(
            keyword.lower() in output.lower()
            for keyword in self.config.completion_keywords
        )
        
        if not is_complete:
            # Validate field presence
            fields = self._extract_fields(output)
            
            # Check required fields
            if self.config.validate_required:
                missing = [
                    field for field in self.config.required_fields
                    if field not in fields
                ]
                if missing:
                    raise ValueError(f"Missing required fields: {', '.join(missing)}")
            
            # Validate field lengths
            for field, value in fields.items():
                if len(value) > self.config.max_field_length:
                    raise ValueError(
                        f"Field '{field}' exceeds max length "
                        f"({len(value)} > {self.config.max_field_length})"
                    )
    
    def get_field_values(self, content: str) -> Dict[str, str]:
        """Helper to extract field values from content
        
        Args:
            content: Content to extract fields from
            
        Returns:
            Dict mapping field names to values
        """
        return self._extract_fields(content) 