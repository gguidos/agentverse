"""
Parser implementations
"""

import json
import logging
from typing import Any, Dict, Optional

from jsonschema import validate
from src.core.agentverse.parser.base import BaseParser, ParserConfig
from src.core.agentverse.exceptions import ParserError

logger = logging.getLogger(__name__)

class JSONParser(BaseParser):
    """JSON parser implementation"""
    
    async def parse(self, content: str) -> Dict[str, Any]:
        """Parse JSON content
        
        Args:
            content: JSON string
            
        Returns:
            Parsed JSON data
            
        Raises:
            ParserError: If parsing fails
        """
        try:
            # Parse JSON
            data = json.loads(content)
            
            # Validate against schema if provided
            if self.config.schema:
                validate(instance=data, schema=self.config.schema)
                
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            raise ParserError(
                message="Failed to parse JSON",
                details={"error": str(e)}
            )
        except Exception as e:
            logger.error(f"Parser error: {e}")
            raise ParserError(
                message="Parser error",
                details={"error": str(e)}
            )
    
    async def format(self, data: Dict[str, Any]) -> str:
        """Format data as JSON string
        
        Args:
            data: Data to format
            
        Returns:
            JSON string
            
        Raises:
            ParserError: If formatting fails
        """
        try:
            return json.dumps(data, indent=2)
        except Exception as e:
            logger.error(f"JSON format error: {e}")
            raise ParserError(
                message="Failed to format JSON",
                details={"error": str(e)}
            ) 