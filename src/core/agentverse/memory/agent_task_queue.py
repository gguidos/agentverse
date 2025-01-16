from typing import Dict, Any, Optional
from redis import Redis
import json
import logging
from src.core.infrastructure.circuit_breaker import circuit_breaker
from src.core.agentverse.memory.agent_metrics import AgentMetricsManager, track_operation_duration, MEMORY_OPERATION_DURATION

logger = logging.getLogger(__name__)

# Task Queue Metrics
TASK_QUEUE_SIZE = Gauge(
    "agent_task_queue_size",
    "Number of tasks in queue",
    ["queue_name"]
)

TASK_OPERATIONS = Counter(
    "agent_task_operations_total",
    "Number of task queue operations",
    ["queue_name", "operation", "status"]  # operation: enqueue/dequeue/peek/clear
)

TASK_OPERATION_DURATION = Histogram(
    "agent_task_operation_duration_seconds",
    "Duration of task queue operations",
    ["queue_name", "operation"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
)

class AgentTaskQueue:
    """Queue for managing agent tasks with metrics and circuit breaker"""
    
    def __init__(self, redis: Redis, queue_name: str = "agent_tasks"):
        self.redis = redis
        self.queue_name = queue_name
        # Initialize queue size metric
        TASK_QUEUE_SIZE.labels(queue_name=queue_name).set(0)
        
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    @track_operation_duration(
        TASK_OPERATION_DURATION,
        {"operation": "enqueue"}
    )
    async def enqueue(self, task: Dict[str, Any]) -> bool:
        """Add task to queue"""
        try:
            task_json = json.dumps(task)
            await self.redis.lpush(self.queue_name, task_json)
            
            # Update metrics
            TASK_OPERATIONS.labels(
                queue_name=self.queue_name,
                operation="enqueue",
                status="success"
            ).inc()
            
            # Update queue size
            size = await self.size()
            TASK_QUEUE_SIZE.labels(queue_name=self.queue_name).set(size)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue task: {str(e)}")
            TASK_OPERATIONS.labels(
                queue_name=self.queue_name,
                operation="enqueue",
                status="error"
            ).inc()
            raise
            
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    @track_operation_duration(
        TASK_OPERATION_DURATION,
        {"operation": "dequeue"}
    )
    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """Get next task from queue"""
        try:
            task_json = await self.redis.rpop(self.queue_name)
            
            if task_json:
                task = json.loads(task_json)
                TASK_OPERATIONS.labels(
                    queue_name=self.queue_name,
                    operation="dequeue",
                    status="success"
                ).inc()
                
                # Update queue size
                size = await self.size()
                TASK_QUEUE_SIZE.labels(queue_name=self.queue_name).set(size)
                
                return task
                
            TASK_OPERATIONS.labels(
                queue_name=self.queue_name,
                operation="dequeue",
                status="empty"
            ).inc()
            return None
            
        except Exception as e:
            logger.error(f"Failed to dequeue task: {str(e)}")
            TASK_OPERATIONS.labels(
                queue_name=self.queue_name,
                operation="dequeue",
                status="error"
            ).inc()
            raise
            
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    @track_operation_duration(
        TASK_OPERATION_DURATION,
        {"operation": "peek"}
    )
    async def peek(self) -> Optional[Dict[str, Any]]:
        """Look at next task without removing it"""
        try:
            task_json = await self.redis.lindex(self.queue_name, -1)
            
            if task_json:
                task = json.loads(task_json)
                TASK_OPERATIONS.labels(
                    queue_name=self.queue_name,
                    operation="peek",
                    status="success"
                ).inc()
                return task
                
            TASK_OPERATIONS.labels(
                queue_name=self.queue_name,
                operation="peek",
                status="empty"
            ).inc()
            return None
            
        except Exception as e:
            logger.error(f"Failed to peek at task: {str(e)}")
            TASK_OPERATIONS.labels(
                queue_name=self.queue_name,
                operation="peek",
                status="error"
            ).inc()
            raise
            
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    @track_operation_duration(
        TASK_OPERATION_DURATION,
        {"operation": "clear"}
    )
    async def clear(self) -> bool:
        """Clear all tasks from queue"""
        try:
            await self.redis.delete(self.queue_name)
            
            TASK_OPERATIONS.labels(
                queue_name=self.queue_name,
                operation="clear",
                status="success"
            ).inc()
            
            # Update queue size
            TASK_QUEUE_SIZE.labels(queue_name=self.queue_name).set(0)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear queue: {str(e)}")
            TASK_OPERATIONS.labels(
                queue_name=self.queue_name,
                operation="clear",
                status="error"
            ).inc()
            raise
            
    @circuit_breaker(failure_threshold=3, recovery_timeout=30)
    async def size(self) -> int:
        """Get number of tasks in queue"""
        try:
            size = await self.redis.llen(self.queue_name)
            return size
            
        except Exception as e:
            logger.error(f"Failed to get queue size: {str(e)}")
            return 0
            
    async def health_check(self) -> bool:
        """Check if queue is healthy"""
        try:
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False 