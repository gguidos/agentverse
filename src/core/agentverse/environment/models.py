"""Environment models"""

from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class EnvironmentStepResult(BaseModel):
    """Result from environment step"""
    output: str = Field(description="Step output")
    logs: List[str] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)
    done: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict) 