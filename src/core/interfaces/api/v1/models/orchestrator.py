from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class AgentTraits(BaseModel):
    """Agent traits configuration"""
    analytical: Optional[float] = None
    creative: Optional[float] = None
    thorough: Optional[float] = None
    skeptical: Optional[float] = None
    concise: Optional[float] = None
    custom_traits: Dict[str, float] = {}

class AgentRoleConfig(BaseModel):
    """Configuration for an agent role"""
    capabilities: List[str]
    traits: AgentTraits = Field(default_factory=AgentTraits)
    priority: int = 1
    min_confidence: float = 0.7
    description: str = ""

class OrchestratorConfigRequest(BaseModel):
    """Request model for orchestrator configuration"""
    name: str
    description: str = ""
    goal_decomposition_strategy: str = "sequential"  # sequential, parallel, adaptive
    coordination_style: str = "directive"  # directive, collaborative, autonomous
    max_coordination_rounds: int = 5
    agent_roles: Dict[str, AgentRoleConfig]
    success_criteria: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {} 