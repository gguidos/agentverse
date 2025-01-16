from typing import Dict, Any, Optional, List, Set
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import logging

from src.core.agentverse.exceptions import AgentStateError

logger = logging.getLogger(__name__)

class AgentStatus:
    """Status constants for agents"""
    INITIALIZING = "initializing"
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    PAUSED = "paused"
    STOPPED = "stopped"

class AgentMetrics(BaseModel):
    """Metrics for agent state"""
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_messages: int = 0
    total_tokens: int = 0
    response_times: List[float] = Field(default_factory=list)
    error_count: int = 0
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks
    
    @property
    def average_response_time(self) -> Optional[float]:
        """Calculate average response time"""
        if not self.response_times:
            return None
        return sum(self.response_times) / len(self.response_times)

class AgentState(BaseModel):
    """Represents the current state of an agent"""
    
    # Identity
    agent_id: str
    agent_type: str = "base_agent"
    name: str = "Agent"
    description: Optional[str] = None
    version: str = "1.0.0"
    
    # Status
    status: str = Field(default=AgentStatus.INITIALIZING)
    current_task: Optional[str] = None
    last_active: datetime = Field(default_factory=datetime.utcnow)
    start_time: datetime = Field(default_factory=datetime.utcnow)
    
    # Capabilities
    capabilities: Set[str] = Field(default_factory=set)
    allowed_actions: Set[str] = Field(default_factory=set)
    receivers: Set[str] = Field(default={"all"})
    
    # Memory and Storage
    memory: Dict[str, Any] = Field(default_factory=dict)
    cache: Dict[str, Any] = Field(default_factory=dict)
    
    # Metrics
    metrics: AgentMetrics = Field(default_factory=AgentMetrics)
    
    # Additional Data
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True
    )
    
    def update(self, **kwargs) -> None:
        """Update state attributes
        
        Args:
            **kwargs: Attributes to update
            
        Raises:
            AgentStateError: If update fails
        """
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.last_active = datetime.utcnow()
        except Exception as e:
            logger.error(f"State update failed: {str(e)}")
            raise AgentStateError(
                message=f"Failed to update state: {str(e)}",
                details={"updates": kwargs}
            )
    
    def track_task(
        self,
        task_id: str,
        success: bool = True,
        duration: Optional[float] = None
    ) -> None:
        """Track task execution
        
        Args:
            task_id: Task identifier
            success: Whether task succeeded
            duration: Optional task duration
        """
        self.metrics.total_tasks += 1
        if success:
            self.metrics.successful_tasks += 1
        else:
            self.metrics.failed_tasks += 1
            
        if duration is not None:
            self.metrics.response_times.append(duration)
    
    def track_error(
        self,
        error: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track error occurrence
        
        Args:
            error: Error message
            details: Optional error details
        """
        self.metrics.error_count += 1
        self.status = AgentStatus.ERROR
        
        error_data = {
            "message": error,
            "timestamp": datetime.utcnow(),
            "details": details or {}
        }
        
        self.metadata.setdefault("errors", []).append(error_data)
    
    def add_capability(self, capability: str) -> None:
        """Add agent capability
        
        Args:
            capability: Capability to add
        """
        self.capabilities.add(capability)
    
    def remove_capability(self, capability: str) -> None:
        """Remove agent capability
        
        Args:
            capability: Capability to remove
        """
        self.capabilities.discard(capability)
    
    def has_capability(self, capability: str) -> bool:
        """Check if agent has capability
        
        Args:
            capability: Capability to check
            
        Returns:
            Whether agent has capability
        """
        return capability in self.capabilities
    
    def clear_memory(self) -> None:
        """Clear agent memory"""
        self.memory.clear()
        self.cache.clear()
    
    def get_uptime(self) -> float:
        """Get agent uptime in seconds
        
        Returns:
            Uptime duration
        """
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics
        
        Returns:
            Metrics dictionary
        """
        metrics = self.metrics.model_dump()
        metrics.update({
            "success_rate": self.metrics.success_rate,
            "avg_response_time": self.metrics.average_response_time,
            "uptime": self.get_uptime()
        })
        return metrics
    
    def model_dump(
        self,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Convert state to dictionary
        
        Returns:
            State dictionary
        """
        data = super().model_dump(*args, **kwargs)
        data.update({
            "last_active": self.last_active.isoformat(),
            "start_time": self.start_time.isoformat(),
            "capabilities": list(self.capabilities),
            "allowed_actions": list(self.allowed_actions),
            "receivers": list(self.receivers),
            "metrics": self.get_metrics()
        })
        return data
    
    def reset(self) -> None:
        """Reset agent state"""
        self.status = AgentStatus.IDLE
        self.current_task = None
        self.last_active = datetime.utcnow()
        self.metrics = AgentMetrics()
        self.clear_memory() 