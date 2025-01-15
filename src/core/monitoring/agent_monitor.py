from prometheus_client import Counter, Histogram, Gauge
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AgentMonitor:
    """Monitors agent health and performance"""
    
    def __init__(self):
        self.metrics = {
            "tasks_processed": Counter(
                "agent_tasks_total",
                "Number of tasks processed",
                ["agent_id", "status"]
            ),
            "response_time": Histogram(
                "agent_response_seconds",
                "Response time in seconds",
                ["agent_id"]
            ),
            "memory_usage": Gauge(
                "agent_memory_bytes",
                "Memory usage in bytes",
                ["agent_id"]
            ),
            "active_tasks": Gauge(
                "agent_active_tasks",
                "Number of active tasks",
                ["agent_id"]
            )
        }
    
    def track_task(self, agent_id: str, status: str):
        """Track task completion status"""
        try:
            self.metrics["tasks_processed"].labels(
                agent_id=agent_id, 
                status=status
            ).inc()
        except Exception as e:
            logger.error(f"Failed to track task: {str(e)}")

    def track_response_time(self, agent_id: str, duration: float):
        """Track agent response time"""
        try:
            self.metrics["response_time"].labels(
                agent_id=agent_id
            ).observe(duration)
        except Exception as e:
            logger.error(f"Failed to track response time: {str(e)}")

    def update_memory_usage(self, agent_id: str, bytes_used: int):
        """Update agent memory usage"""
        try:
            self.metrics["memory_usage"].labels(
                agent_id=agent_id
            ).set(bytes_used)
        except Exception as e:
            logger.error(f"Failed to update memory usage: {str(e)}")

    def update_active_tasks(self, agent_id: str, count: int):
        """Update number of active tasks"""
        try:
            self.metrics["active_tasks"].labels(
                agent_id=agent_id
            ).set(count)
        except Exception as e:
            logger.error(f"Failed to update active tasks: {str(e)}") 