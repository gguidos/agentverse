"""Metrics Collection Module"""

from typing import Dict, Any, Optional, List, Union, ContextManager
from pydantic import BaseModel, Field
from datetime import datetime
import prometheus_client as prom
import contextlib
import time

class MetricsConfig(BaseModel):
    """Metrics configuration"""
    enabled: bool = True
    prefix: str = "agentverse"
    labels: Dict[str, str] = Field(default_factory=dict)

class MetricsCollector:
    """Metrics collection and management"""
    
    def __init__(self, config: Optional[MetricsConfig] = None):
        self.config = config or MetricsConfig()
        
        # Agent metrics
        self.agent_latency = prom.Histogram(
            f"{self.config.prefix}_agent_latency_seconds",
            "Agent operation latency in seconds",
            ["agent_id", "operation"]
        )
        self.agent_requests = prom.Counter(
            f"{self.config.prefix}_agent_requests_total",
            "Total number of agent requests",
            ["agent_id", "operation"]
        )
        self.agent_errors = prom.Counter(
            f"{self.config.prefix}_agent_errors_total",
            "Total number of agent errors",
            ["agent_id", "operation", "error_type"]
        )
        
        # System metrics
        self.memory_usage = prom.Gauge(
            f"{self.config.prefix}_memory_bytes",
            "Memory usage in bytes",
            ["type"]
        )
        self.cpu_usage = prom.Gauge(
            f"{self.config.prefix}_cpu_usage",
            "CPU usage percentage",
            ["type"]
        )
        
        # Message metrics
        self.message_throughput = prom.Counter(
            f"{self.config.prefix}_message_throughput_total",
            "Total message throughput",
            ["type"]
        )
        self.queue_size = prom.Gauge(
            f"{self.config.prefix}_queue_size",
            "Current queue size",
            ["queue"]
        )
    
    def record_agent_latency(
        self,
        agent_id: str,
        operation: str,
        latency: float
    ) -> None:
        """Record agent operation latency"""
        if self.config.enabled:
            self.agent_latency.labels(
                agent_id=agent_id,
                operation=operation
            ).observe(latency)
    
    def record_agent_request(
        self,
        agent_id: str,
        operation: str
    ) -> None:
        """Record agent request"""
        if self.config.enabled:
            self.agent_requests.labels(
                agent_id=agent_id,
                operation=operation
            ).inc()
    
    def record_agent_error(
        self,
        agent_id: str,
        operation: str,
        error_type: str
    ) -> None:
        """Record agent error"""
        if self.config.enabled:
            self.agent_errors.labels(
                agent_id=agent_id,
                operation=operation,
                error_type=error_type
            ).inc()
    
    @contextlib.contextmanager
    def track_resource_usage(self, resource_type: str) -> ContextManager:
        """Track resource usage within a context"""
        try:
            start_time = time.time()
            yield
        finally:
            if self.config.enabled:
                duration = time.time() - start_time
                self.memory_usage.labels(type=resource_type).set(duration)

class PrometheusExporter:
    """Prometheus metrics exporter"""
    
    def __init__(self, port: int = 8000):
        self.port = port
        
    def start(self) -> None:
        """Start Prometheus HTTP server"""
        prom.start_http_server(self.port) 