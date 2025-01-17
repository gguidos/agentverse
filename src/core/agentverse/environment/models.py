"""Environment models"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class EnvironmentStepResult(BaseModel):
    """Result of an environment step"""
    
    output: str
    logs: List[str] = []
    metrics: Dict[str, Any] = {}
    done: bool = False
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow) 