"""Base Environment Module"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pydantic import BaseModel, Field

from src.core.agentverse.message import Message

class EnvironmentState(BaseModel):
    """Environment state model"""
    
    # Status tracking
    status: str = "initialized"
    error_count: int = 0
    last_update: Optional[datetime] = None
    last_error: Optional[str] = None
    
    # Agent tracking
    agents: Set[str] = Field(default_factory=set)
    active_agent: Optional[str] = None
    
    # Message tracking
    last_messages: List[Message] = Field(default_factory=list)
    message_history: List[Message] = Field(default_factory=list)
    
    # Performance metrics
    metrics: Dict[str, Any] = Field(default_factory=dict)
    
    # Custom state data
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "arbitrary_types_allowed": True
    }

class EnvironmentConfig(BaseModel):
    """Environment configuration"""
    
    name: str = Field(description="Environment name")
    description: Optional[str] = None
    max_turns: Optional[int] = None
    max_messages: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseEnvironment(ABC):
    """Abstract base class for environments"""
    
    def __init__(
        self,
        config: Optional[EnvironmentConfig] = None,
        **kwargs
    ):
        self.config = config or EnvironmentConfig(**kwargs)
        self.state = EnvironmentState()
        self._locks = {}  # Agent locks for concurrency control
    
    @abstractmethod
    async def step(self, message: Message) -> Dict[str, Any]:
        """Process one environment step"""
        pass
    
    @abstractmethod
    def add_agents(self, agents: List["BaseAgent"]) -> None:
        """Add agents to environment"""
        pass
    
    def reset(self) -> None:
        """Reset environment state"""
        self.state = EnvironmentState()
    
    async def is_done(self) -> bool:
        """Check if environment is done"""
        if self.state.max_turns and self.state.current_turn >= self.state.max_turns:
            return True
        return False
    
    async def get_metrics(self) -> Dict[str, float]:
        """Get environment metrics"""
        return self.state.metrics.copy()
    
    async def validate_state(self) -> bool:
        """Validate environment state"""
        return True

__all__ = [
    "EnvironmentState",
    "EnvironmentConfig", 
    "BaseEnvironment"
] 