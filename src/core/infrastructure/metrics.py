from prometheus_client import Counter, Summary, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Request, Response
from starlette.responses import Response

# Create a router for metrics
metrics_router = APIRouter()

# Define metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Number of currently active HTTP requests",
    ["method"]
)

@metrics_router.get("/metrics")
async def metrics():
    """Expose Prometheus metrics."""
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

def track_request(method: str, endpoint: str, status_code: int, duration: float):
    """Track request metrics."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

def track_active_request(method: str, delta: int = 1):
    """Track active requests."""
    ACTIVE_REQUESTS.labels(method=method).inc(delta)
