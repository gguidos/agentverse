from typing import Dict, Any, Optional, ClassVar, List
from pydantic import BaseModel, Field, ConfigDict
from prometheus_client import Counter, Histogram, Gauge, Summary
from datetime import datetime
import logging
import time

from src.core.agentverse.message.base import Message
from src.core.agentverse.exceptions import MonitoringError

logger = logging.getLogger(__name__)

class AgentMetrics(BaseModel):
    """Metrics for agent monitoring"""
    tasks_total: int = 0
    tasks_success: int = 0
    tasks_failed: int = 0
    response_times: List[float] = Field(default_factory=list)
    memory_usage: Dict[str, int] = Field(default_factory=dict)
    active_tasks: int = 0
    last_activity: Optional[datetime] = None
    errors: Dict[str, int] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )

class AgentMonitor:
    """Monitors agent health and performance"""
    
    name: ClassVar[str] = "agent_monitor"
    description: ClassVar[str] = "Agent health and performance monitor"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(self, namespace: str = "agentverse"):
        """Initialize monitor
        
        Args:
            namespace: Metrics namespace
        """
        self.namespace = namespace
        self._setup_metrics()
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        logger.info(f"Initialized {self.name} v{self.version}")
    
    def _setup_metrics(self) -> None:
        """Setup Prometheus metrics"""
        try:
            self.metrics = {
                # Task metrics
                "tasks_processed": Counter(
                    f"{self.namespace}_tasks_total",
                    "Number of tasks processed",
                    ["agent_id", "status"]
                ),
                "task_duration": Histogram(
                    f"{self.namespace}_task_duration_seconds",
                    "Task processing duration in seconds",
                    ["agent_id", "status"],
                    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
                ),
                
                # Response metrics
                "response_time": Histogram(
                    f"{self.namespace}_response_seconds",
                    "Response time in seconds",
                    ["agent_id"],
                    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
                ),
                "response_size": Summary(
                    f"{self.namespace}_response_bytes",
                    "Response size in bytes",
                    ["agent_id"]
                ),
                
                # Resource metrics
                "memory_usage": Gauge(
                    f"{self.namespace}_memory_bytes",
                    "Memory usage in bytes",
                    ["agent_id", "type"]
                ),
                "active_tasks": Gauge(
                    f"{self.namespace}_active_tasks",
                    "Number of active tasks",
                    ["agent_id"]
                ),
                
                # Error metrics
                "errors_total": Counter(
                    f"{self.namespace}_errors_total",
                    "Number of errors",
                    ["agent_id", "type"]
                )
            }
        except Exception as e:
            logger.error(f"Failed to setup metrics: {str(e)}")
            raise MonitoringError(
                message=f"Metrics setup failed: {str(e)}",
                details={"namespace": self.namespace}
            )
    
    def track_task(
        self,
        agent_id: str,
        status: str,
        duration: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """Track task completion
        
        Args:
            agent_id: Agent identifier
            status: Task status
            duration: Optional task duration
            error: Optional error message
        """
        try:
            # Update Prometheus metrics
            self.metrics["tasks_processed"].labels(
                agent_id=agent_id,
                status=status
            ).inc()
            
            if duration is not None:
                self.metrics["task_duration"].labels(
                    agent_id=agent_id,
                    status=status
                ).observe(duration)
            
            # Update agent metrics
            metrics = self._get_agent_metrics(agent_id)
            metrics.tasks_total += 1
            if status == "success":
                metrics.tasks_success += 1
            elif status == "failed":
                metrics.tasks_failed += 1
                if error:
                    metrics.errors[error] = metrics.errors.get(error, 0) + 1
            
            metrics.last_activity = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to track task: {str(e)}")
    
    def track_response(
        self,
        agent_id: str,
        message: Message,
        duration: float
    ) -> None:
        """Track agent response
        
        Args:
            agent_id: Agent identifier
            message: Response message
            duration: Response duration
        """
        try:
            # Update Prometheus metrics
            self.metrics["response_time"].labels(
                agent_id=agent_id
            ).observe(duration)
            
            response_size = len(message.content.encode())
            self.metrics["response_size"].labels(
                agent_id=agent_id
            ).observe(response_size)
            
            # Update agent metrics
            metrics = self._get_agent_metrics(agent_id)
            metrics.response_times.append(duration)
            metrics.last_activity = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Failed to track response: {str(e)}")
    
    def update_memory_usage(
        self,
        agent_id: str,
        usage: Dict[str, int]
    ) -> None:
        """Update agent memory usage
        
        Args:
            agent_id: Agent identifier
            usage: Memory usage by type
        """
        try:
            # Update Prometheus metrics
            for type_, bytes_used in usage.items():
                self.metrics["memory_usage"].labels(
                    agent_id=agent_id,
                    type=type_
                ).set(bytes_used)
            
            # Update agent metrics
            metrics = self._get_agent_metrics(agent_id)
            metrics.memory_usage.update(usage)
            
        except Exception as e:
            logger.error(f"Failed to update memory usage: {str(e)}")
    
    def update_active_tasks(
        self,
        agent_id: str,
        count: int
    ) -> None:
        """Update number of active tasks
        
        Args:
            agent_id: Agent identifier
            count: Active task count
        """
        try:
            # Update Prometheus metrics
            self.metrics["active_tasks"].labels(
                agent_id=agent_id
            ).set(count)
            
            # Update agent metrics
            metrics = self._get_agent_metrics(agent_id)
            metrics.active_tasks = count
            
        except Exception as e:
            logger.error(f"Failed to update active tasks: {str(e)}")
    
    def track_error(
        self,
        agent_id: str,
        error_type: str,
        error: str
    ) -> None:
        """Track agent error
        
        Args:
            agent_id: Agent identifier
            error_type: Type of error
            error: Error message
        """
        try:
            # Update Prometheus metrics
            self.metrics["errors_total"].labels(
                agent_id=agent_id,
                type=error_type
            ).inc()
            
            # Update agent metrics
            metrics = self._get_agent_metrics(agent_id)
            metrics.errors[error] = metrics.errors.get(error, 0) + 1
            
        except Exception as e:
            logger.error(f"Failed to track error: {str(e)}")
    
    def _get_agent_metrics(
        self,
        agent_id: str
    ) -> AgentMetrics:
        """Get or create agent metrics
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent metrics
        """
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = AgentMetrics()
        return self.agent_metrics[agent_id]
    
    def get_metrics(
        self,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get monitoring metrics
        
        Args:
            agent_id: Optional agent to get metrics for
            
        Returns:
            Monitoring metrics
        """
        if agent_id:
            metrics = self._get_agent_metrics(agent_id)
            data = metrics.model_dump()
            
            # Add computed metrics
            if metrics.response_times:
                data["avg_response_time"] = (
                    sum(metrics.response_times) /
                    len(metrics.response_times)
                )
            
            if metrics.tasks_total > 0:
                data["success_rate"] = (
                    metrics.tasks_success /
                    metrics.tasks_total
                )
            
            return data
        
        return {
            agent_id: self.get_metrics(agent_id)
            for agent_id in self.agent_metrics
        }
    
    def reset(
        self,
        agent_id: Optional[str] = None
    ) -> None:
        """Reset monitoring state
        
        Args:
            agent_id: Optional agent to reset
        """
        if agent_id:
            self.agent_metrics.pop(agent_id, None)
        else:
            self.agent_metrics.clear()
        logger.info(
            f"Reset {self.name} "
            f"for {agent_id if agent_id else 'all agents'}"
        ) 