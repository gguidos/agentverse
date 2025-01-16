"""Memory types and shared models"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field

class MemoryConfig(BaseModel):
    """Memory configuration"""
    name: str = "default"
    backend_type: str
    backend_name: str
    backend_config: Optional[Dict[str, Any]] = None
    manipulator_config: Optional[Dict[str, Any]] = None
    max_size: Optional[int] = None
    ttl: Optional[int] = None
    
    class Config:
        extra = "allow"

class MemoryData(BaseModel):
    """Memory data model"""
    content: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True 