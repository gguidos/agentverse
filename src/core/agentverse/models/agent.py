"""Agent Models Module"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class AgentProfile(BaseModel):
    """Agent profile configuration"""
    name: str
    description: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AgentCapability(BaseModel):
    """Agent capability definition"""
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requirements: List[str] = Field(default_factory=list)
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentMetric(BaseModel):
    """Agent performance metrics"""
    agent_id: str
    metric_type: str
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict) 