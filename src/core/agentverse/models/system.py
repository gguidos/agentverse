"""System Models Module"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class EnvironmentType(str, Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

class SystemConfig(BaseModel):
    """System configuration"""
    environment: EnvironmentType = EnvironmentType.DEVELOPMENT
    log_level: LogLevel = LogLevel.INFO
    max_agents: int = 10
    timeout: int = 30
    debug: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Environment(BaseModel):
    """Environment configuration"""
    type: EnvironmentType
    variables: Dict[str, str] = Field(default_factory=dict)
    features: Dict[str, bool] = Field(default_factory=dict)
    limits: Dict[str, int] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Resource(BaseModel):
    """System resource configuration"""
    name: str
    type: str
    capacity: Optional[int] = None
    used: int = 0
    available: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def calculate_available(self) -> int:
        """Calculate available resources"""
        if self.capacity is not None:
            self.available = max(0, self.capacity - self.used)
        return self.available 