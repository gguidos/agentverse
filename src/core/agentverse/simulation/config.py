"""Simulation configuration"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SimulationConfig(BaseModel):
    """Simulation configuration"""
    name: str = Field(description="Simulation name")
    description: Optional[str] = None
    max_steps: int = Field(default=100, description="Maximum simulation steps")
    save_history: bool = Field(default=True, description="Save simulation history")
    environment: Dict[str, Any] = Field(description="Environment configuration")
    agents: List[Dict[str, Any]] = Field(description="Agent configurations")
    metadata: Dict[str, Any] = Field(default_factory=dict) 