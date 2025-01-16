from typing import Dict, Any, Optional, List, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.exceptions import ActionError

logger = logging.getLogger(__name__)

class ActionStatus:
    """Status constants for agent actions"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ActionMetadata(BaseModel):
    """Metadata for agent actions"""
    source: Optional[str] = None
    priority: int = 0
    tags: List[str] = Field(default_factory=list)
    retry_count: int = 0
    duration: Optional[float] = None
    error: Optional[str] = None
    
    model_config = ConfigDict(
        extra="allow"
    )

class AgentAction(BaseModel):
    """Represents an action an agent decides to take"""
    tool: str
    input: Dict[str, Any]
    output: Optional[Any] = None
    status: str = Field(default=ActionStatus.PENDING)
    metadata: ActionMetadata = Field(default_factory=ActionMetadata)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )
    
    def complete(
        self,
        output: Any,
        duration: Optional[float] = None
    ) -> None:
        """Mark action as completed
        
        Args:
            output: Action output
            duration: Optional execution duration
        """
        self.output = output
        self.status = ActionStatus.COMPLETED
        if duration:
            self.metadata.duration = duration
    
    def fail(
        self,
        error: str,
        retry: bool = True
    ) -> None:
        """Mark action as failed
        
        Args:
            error: Error message
            retry: Whether action can be retried
        """
        self.status = ActionStatus.FAILED
        self.metadata.error = error
        if retry:
            self.metadata.retry_count += 1
    
    def cancel(self) -> None:
        """Mark action as cancelled"""
        self.status = ActionStatus.CANCELLED
    
    def can_retry(
        self,
        max_retries: int
    ) -> bool:
        """Check if action can be retried
        
        Args:
            max_retries: Maximum retry count
            
        Returns:
            Whether action can be retried
        """
        return (
            self.status == ActionStatus.FAILED and
            self.metadata.retry_count < max_retries
        )
    
    def model_dump(
        self,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Custom serialization
        
        Returns:
            Serialized action
        """
        return {
            "tool": self.tool,
            "input": self.input,
            "output": self.output,
            "status": self.status,
            "metadata": self.metadata.model_dump(),
            "timestamp": self.timestamp.isoformat()
        }

class AgentStep(BaseModel):
    """Represents a single step in agent's reasoning"""
    action: Optional[AgentAction] = None
    observation: Optional[Any] = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error: Optional[str] = None
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )
    
    def complete(
        self,
        observation: Any
    ) -> None:
        """Complete step with observation
        
        Args:
            observation: Step observation
        """
        self.observation = observation
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.duration = (
                self.end_time - self.start_time
            ).total_seconds()
    
    def fail(
        self,
        error: str
    ) -> None:
        """Mark step as failed
        
        Args:
            error: Error message
        """
        self.error = error
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.duration = (
                self.end_time - self.start_time
            ).total_seconds()
    
    def model_dump(
        self,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Custom serialization
        
        Returns:
            Serialized step
        """
        return {
            "action": (
                self.action.model_dump()
                if self.action else None
            ),
            "observation": str(self.observation) if self.observation else None,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "error": self.error
        }
    
    def __repr__(self) -> str:
        return (
            f"AgentStep("
            f"action={self.action.tool if self.action else None}, "
            f"duration={self.duration:.2f if self.duration else None}s, "
            f"error={self.error is not None})"
        )

class ActionSequence(BaseModel):
    """Sequence of agent actions and steps"""
    steps: List[AgentStep] = Field(default_factory=list)
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None
    error_count: int = 0
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
    
    def add_step(
        self,
        step: AgentStep
    ) -> None:
        """Add step to sequence
        
        Args:
            step: Step to add
        """
        self.steps.append(step)
        if step.error:
            self.error_count += 1
    
    def complete(self) -> None:
        """Mark sequence as completed"""
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.total_duration = (
                self.end_time - self.start_time
            ).total_seconds()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get sequence metrics
        
        Returns:
            Metrics dictionary
        """
        step_durations = [
            s.duration for s in self.steps
            if s.duration is not None
        ]
        
        return {
            "total_steps": len(self.steps),
            "error_count": self.error_count,
            "total_duration": self.total_duration,
            "avg_step_duration": (
                sum(step_durations) / len(step_durations)
                if step_durations else None
            ),
            "error_rate": (
                self.error_count / len(self.steps)
                if self.steps else 0
            )
        } 