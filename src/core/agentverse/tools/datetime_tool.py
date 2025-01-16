from datetime import datetime, timedelta
from typing import Dict, Any, ClassVar, Optional
from src.core.agentverse.tools.base import BaseTool, ToolResult, ToolConfig, ToolExecutionError
import pytz
import logging

logger = logging.getLogger(__name__)

class DateTimeToolConfig(ToolConfig):
    """DateTime tool specific configuration"""
    default_timezone: str = "UTC"
    default_format: str = "%Y-%m-%d %H:%M:%S"
    allow_future_dates: bool = True
    max_past_years: int = 100

class DateTimeTool(BaseTool):
    """Tool for datetime operations and formatting"""
    
    name: ClassVar[str] = "datetime"
    description: ClassVar[str] = """
    Get current time, format dates, calculate time differences, and handle timezones.
    Useful for time-based queries and calculations.
    """
    version: ClassVar[str] = "1.1.0"
    parameters: ClassVar[Dict[str, Any]] = {
        "operation": {
            "type": "string",
            "description": "The datetime operation to perform",
            "required": True,
            "enum": ["current_time", "format_date", "time_diff", "convert_timezone"]
        },
        "format": {
            "type": "string",
            "description": "Output format (e.g., 'YYYY-MM-DD HH:mm:ss')",
            "required": False
        },
        "timezone": {
            "type": "string",
            "description": "Timezone name (e.g., 'UTC', 'America/New_York')",
            "required": False
        },
        "date_string": {
            "type": "string",
            "description": "Date string to parse (ISO format)",
            "required": False
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
    
    async def execute(
        self, 
        operation: str,
        format: Optional[str] = None,
        timezone: Optional[str] = None,
        date_string: Optional[str] = None
    ) -> ToolResult:
        """Execute datetime operations"""
        try:
            # Validate inputs
            format = self._validate_format(format or self.config.default_format)
            timezone = self._validate_timezone(timezone or self.config.default_timezone)
            
            if operation == "current_time":
                tz = pytz.timezone(timezone)
                current = datetime.now(tz)
                return ToolResult(
                    success=True,
                    result=current.strftime(format),
                    metadata={
                        "timezone": timezone,
                        "format": format,
                        "timestamp_utc": current.astimezone(pytz.UTC).isoformat()
                    }
                )
                
            elif operation == "format_date":
                if not date_string:
                    raise ValueError("date_string is required for format_date operation")
                    
                dt = datetime.fromisoformat(date_string)
                return ToolResult(
                    success=True,
                    result=dt.strftime(format),
                    metadata={
                        "format": format,
                        "original_date": date_string
                    }
                )
                
            elif operation == "time_diff":
                if not date_string:
                    raise ValueError("date_string is required for time_diff operation")
                    
                dt = datetime.fromisoformat(date_string)
                now = datetime.now(pytz.UTC)
                diff = now - dt.replace(tzinfo=pytz.UTC)
                
                # Calculate human-readable difference
                days = diff.days
                hours = diff.seconds // 3600
                minutes = (diff.seconds % 3600) // 60
                seconds = diff.seconds % 60
                
                return ToolResult(
                    success=True,
                    result={
                        "total_seconds": int(diff.total_seconds()),
                        "components": {
                            "days": days,
                            "hours": hours,
                            "minutes": minutes,
                            "seconds": seconds
                        },
                        "human_readable": self._format_time_diff(days, hours, minutes, seconds)
                    },
                    metadata={
                        "reference_date": date_string,
                        "current_time_utc": now.isoformat()
                    }
                )
                
            elif operation == "convert_timezone":
                if not date_string:
                    raise ValueError("date_string is required for convert_timezone operation")
                    
                dt = datetime.fromisoformat(date_string)
                target_tz = pytz.timezone(timezone)
                converted = dt.astimezone(target_tz)
                
                return ToolResult(
                    success=True,
                    result=converted.strftime(format),
                    metadata={
                        "source_timezone": str(dt.tzinfo or "naive"),
                        "target_timezone": str(timezone),
                        "format": format,
                        "original_date": date_string
                    }
                )
                
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"DateTime tool error: {str(e)}")
            raise ToolExecutionError(f"DateTime operation failed: {str(e)}", e)
            
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