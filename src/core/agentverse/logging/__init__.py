"""
AgentVerse logging module
"""

import logging
import os
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel

class LogConfig(BaseModel):
    """Logging configuration"""
    
    log_dir: str = "logs"
    log_level: str = "INFO"
    enable_console: bool = True
    enable_file: bool = True
    enable_json: bool = True
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "log_dir": "logs",
                "log_level": "INFO",
                "enable_console": True
            }]
        }
    }

class JsonLogFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format record as JSON"""
        data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if hasattr(record, "metadata"):
            data["metadata"] = record.metadata
            
        return json.dumps(data)

class Logger:
    """AgentVerse logger implementation"""
    
    def __init__(self, config: Optional[LogConfig] = None):
        self.config = config or LogConfig()
        
        # Create logger
        self.logger = logging.getLogger("agentverse")
        self.logger.setLevel(self.config.log_level)
        
        # Create log directory
        if not os.path.exists(self.config.log_dir):
            os.makedirs(self.config.log_dir)
        
        # Add console handler
        if self.config.enable_console:
            console = logging.StreamHandler()
            console.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(console)
        
        # Add file handler
        if self.config.enable_file:
            file_handler = logging.FileHandler(
                os.path.join(self.config.log_dir, "agentverse.log")
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(file_handler)
        
        # Add JSON handler
        if self.config.enable_json:
            json_handler = logging.FileHandler(
                os.path.join(self.config.log_dir, "agentverse.json")
            )
            json_handler.setFormatter(JsonLogFormatter())
            self.logger.addHandler(json_handler)
    
    def log(self, level: int, msg: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log message with optional metadata"""
        extra = {"metadata": metadata} if metadata else None
        self.logger.log(level, msg, extra=extra)
    
    def debug(self, msg: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message"""
        self.log(logging.DEBUG, msg, metadata)
    
    def info(self, msg: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log info message"""
        self.log(logging.INFO, msg, metadata)
    
    def warning(self, msg: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message"""
        self.log(logging.WARNING, msg, metadata)
    
    def error(self, msg: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log error message"""
        self.log(logging.ERROR, msg, metadata)

# Global logger instance
logger = Logger()

def get_logger() -> Logger:
    """Get global logger instance"""
    return logger 