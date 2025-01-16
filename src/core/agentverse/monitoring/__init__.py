"""
Monitoring Module

This module provides monitoring and observability features for AgentVerse:

1. Metrics Collection:
   - Agent Metrics: Performance, usage, latency
   - System Metrics: Resources, throughput, errors
   - Memory Metrics: Usage, operations, cache hits
   - Message Metrics: Volume, latency, errors

2. Monitoring Types:
   - Performance Monitoring
   - Resource Monitoring
   - Health Monitoring
   - Error Monitoring

3. Integration Support:
   - Prometheus Integration
   - Grafana Dashboards
   - Custom Exporters
   - Alert Management

Example Usage:
    ```python
    from src.core.agentverse.monitoring import (
        MetricsCollector,
        HealthCheck,
        AlertManager
    )

    # Collect agent metrics
    metrics = MetricsCollector()
    metrics.record_agent_latency(
        agent_id="agent_1",
        operation="chat",
        latency=0.5
    )

    # Perform health check
    health = HealthCheck()
    status = await health.check_system_health()
    if not status.is_healthy:
        await AlertManager.send_alert(
            level="warning",
            message=f"System health check failed: {status.details}"
        )

    # Monitor resource usage
    with metrics.track_resource_usage("memory"):
        result = await process_large_dataset()
    ```

Metrics Structure:
    ```
    agentverse_metrics
    ├── agent
    │   ├── latency_seconds
    │   ├── requests_total
    │   └── errors_total
    ├── system
    │   ├── memory_bytes
    │   ├── cpu_usage
    │   └── uptime_seconds
    ├── memory
    │   ├── operations_total
    │   ├── cache_hits_ratio
    │   └── size_bytes
    └── message
        ├── throughput
        ├── queue_size
        └── processing_time
    ```
"""

from src.core.agentverse.monitoring.metrics import (
    MetricsCollector,
    PrometheusExporter
)
from src.core.agentverse.monitoring.health import (
    HealthCheck,
    HealthStatus
)
from src.core.agentverse.monitoring.alerts import (
    AlertManager,
    AlertLevel,
    Alert
)
from src.core.agentverse.monitoring.tracing import (
    TracingManager,
    Span,
    TraceContext
)

__all__ = [
    # Metrics
    'MetricsCollector',
    'PrometheusExporter',
    
    # Health
    'HealthCheck',
    'HealthStatus',
    
    # Alerts
    'AlertManager',
    'AlertLevel',
    'Alert',
    
    # Tracing
    'TracingManager',
    'Span',
    'TraceContext'
]

# Version
__version__ = "1.0.0" 