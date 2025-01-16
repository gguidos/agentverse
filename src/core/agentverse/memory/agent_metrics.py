from prometheus_client import Counter, Gauge, Histogram
import time
from functools import wraps
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Message Metrics
MESSAGE_COUNT = Counter(
    "agent_messages_total",
    "Number of messages processed",
    ["agent_id", "direction", "message_type"]  # direction: sent/received
)

MESSAGE_SIZE = Histogram(
    "agent_message_size_bytes",
    "Size of messages in bytes",
    ["agent_id", "message_type"],
    buckets=[100, 500, 1000, 5000, 10000]
)

# Memory Metrics
MEMORY_SIZE = Gauge(
    "agent_memory_size_bytes",
    "Size of agent memory in bytes",
    ["agent_id", "memory_type"]  # memory_type: short_term/long_term/vector
)

MEMORY_OPERATIONS = Counter(
    "agent_memory_operations_total",
    "Number of memory operations",
    ["agent_id", "operation", "status"]  # operation: store/retrieve/clear
)

MEMORY_OPERATION_DURATION = Histogram(
    "agent_memory_operation_duration_seconds",
    "Duration of memory operations",
    ["agent_id", "operation"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

# Vector Search Metrics
VECTOR_SEARCH_REQUESTS = Counter(
    "agent_vector_search_total",
    "Number of vector similarity searches",
    ["agent_id", "backend"]
)

VECTOR_SEARCH_DURATION = Histogram(
    "agent_vector_search_duration_seconds",
    "Duration of vector similarity searches",
    ["agent_id", "backend"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

# Health Metrics
HEALTH_STATUS = Gauge(
    "agent_component_health",
    "Health status of agent components",
    ["agent_id", "component"]  # component: redis/mongo/vector_store
)

def track_operation_duration(metric: Histogram, labels: Optional[dict] = None):
    """Decorator to track operation duration"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                raise
        return wrapper
    return decorator

class AgentMetricsManager:
    """Manager for agent-related metrics"""
    
    @staticmethod
    def record_message(agent_id: str, direction: str, message_type: str, size: int):
        """Record message metrics"""
        try:
            MESSAGE_COUNT.labels(
                agent_id=agent_id,
                direction=direction,
                message_type=message_type
            ).inc()
            
            MESSAGE_SIZE.labels(
                agent_id=agent_id,
                message_type=message_type
            ).observe(size)
        except Exception as e:
            logger.error(f"Failed to record message metrics: {str(e)}")
    
    @staticmethod
    def record_memory_operation(agent_id: str, operation: str, status: str = "success"):
        """Record memory operation metrics"""
        try:
            MEMORY_OPERATIONS.labels(
                agent_id=agent_id,
                operation=operation,
                status=status
            ).inc()
        except Exception as e:
            logger.error(f"Failed to record memory operation metrics: {str(e)}")
    
    @staticmethod
    def update_memory_size(agent_id: str, memory_type: str, size: float):
        """Update memory size gauge"""
        try:
            MEMORY_SIZE.labels(
                agent_id=agent_id,
                memory_type=memory_type
            ).set(size)
        except Exception as e:
            logger.error(f"Failed to update memory size metrics: {str(e)}")
    
    @staticmethod
    def record_vector_search(agent_id: str, backend: str):
        """Record vector search metrics"""
        try:
            VECTOR_SEARCH_REQUESTS.labels(
                agent_id=agent_id,
                backend=backend
            ).inc()
        except Exception as e:
            logger.error(f"Failed to record vector search metrics: {str(e)}")
    
    @staticmethod
    def update_health_status(agent_id: str, component: str, status: float):
        """Update component health status"""
        try:
            HEALTH_STATUS.labels(
                agent_id=agent_id,
                component=component
            ).set(status)
        except Exception as e:
            logger.error(f"Failed to update health status metrics: {str(e)}")

    @staticmethod
    def get_metrics_summary(agent_id: str) -> dict:
        """Get summary of agent metrics"""
        try:
            return {
                "messages": {
                    "sent": MESSAGE_COUNT.labels(agent_id=agent_id, direction="sent", message_type="all")._value.get(),
                    "received": MESSAGE_COUNT.labels(agent_id=agent_id, direction="received", message_type="all")._value.get()
                },
                "memory": {
                    "operations": MEMORY_OPERATIONS.labels(agent_id=agent_id, operation="all", status="success")._value.get(),
                    "size": {
                        "short_term": MEMORY_SIZE.labels(agent_id=agent_id, memory_type="short_term")._value,
                        "long_term": MEMORY_SIZE.labels(agent_id=agent_id, memory_type="long_term")._value,
                        "vector": MEMORY_SIZE.labels(agent_id=agent_id, memory_type="vector")._value
                    }
                },
                "vector_searches": VECTOR_SEARCH_REQUESTS.labels(agent_id=agent_id, backend="all")._value.get(),
                "health": {
                    component: HEALTH_STATUS.labels(agent_id=agent_id, component=component)._value
                    for component in ["redis", "mongo", "vector_store"]
                }
            }
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {str(e)}")
            return {} 