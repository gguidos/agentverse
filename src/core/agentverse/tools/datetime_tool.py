from datetime import datetime
from typing import Dict, Any, ClassVar, Optional
from src.core.agentverse.tools.base import BaseTool, ToolResult, ToolConfig
import pytz
import logging
from src.core.agentverse.tools.registry import tool_registry
from src.core.agentverse.tools.types import AgentCapability, ToolType

logger = logging.getLogger(__name__)

class DateTimeToolConfig(ToolConfig):
    """DateTime tool specific configuration"""
    default_timezone: str = "UTC"
    default_format: str = "%Y-%m-%d %H:%M:%S"
    allow_future_dates: bool = True
    max_past_years: int = 100

@tool_registry.register(AgentCapability.DATETIME, ToolType.SIMPLE)
class DateTimeTool(BaseTool):
    """Tool for datetime operations"""
    name: ClassVar[str] = "datetime"
    description: ClassVar[str] = """
    Get current time, format dates, calculate time differences, and handle timezones.
    Useful for time-based queries and calculations.
    """
    version: ClassVar[str] = "1.1.0"
    required_permissions: ClassVar[list] = []
    parameters: ClassVar[Dict[str, Any]] = {
        "format": {
            "type": "string",
            "description": "Output datetime format",
            "default": "%Y-%m-%d %H:%M:%S"
        }
    }
    
    def __init__(self, config: Optional[DateTimeToolConfig] = None):
        super().__init__(config=config or DateTimeToolConfig())
        
    def _validate_timezone(self, timezone: str) -> str:
        """Validate and return timezone"""
        try:
            return str(pytz.timezone(timezone))
        except Exception as e:
            logger.error(f"Invalid timezone {timezone}: {str(e)}")
            return self.config.default_timezone
            
    def _validate_format(self, format: str) -> str:
        """Validate and return date format"""
        try:
            # Test the format with current time
            datetime.now().strftime(format)
            return format
        except Exception as e:
            logger.warning(f"Invalid date format {format}, using default: {str(e)}")
            return self.config.default_format
    
    async def execute(self, format: str = "%Y-%m-%d %H:%M:%S") -> ToolResult:
        """Get current datetime in specified format"""
        try:
            result = datetime.now().strftime(format)
            return ToolResult(
                success=True,
                result=result,
                metadata={
                    "format": format
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )
            
    def _format_time_diff(self, days: int, hours: int, minutes: int, seconds: int) -> str:
        """Format time difference in human readable format"""
        parts = []
        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds or not parts:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
            
        return ", ".join(parts) 