from circuitbreaker import circuit
from functools import wraps
import logging
from prometheus_client import Counter

logger = logging.getLogger(__name__)

CIRCUIT_BREAKER_FAILURES = Counter(
    "circuit_breaker_failures_total",
    "Number of circuit breaker failures",
    ["service", "operation"]
)

def circuit_breaker(failure_threshold=5, recovery_timeout=60, fallback_function=None):
    """
    Custom circuit breaker decorator.
    
    Args:
        failure_threshold (int): Number of failures before circuit opens
        recovery_timeout (int): Seconds to wait before attempting recovery
        fallback_function (callable): Function to call when circuit is open
    """
    def circuit_decorator(func):
        @circuit(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            name=f"circuit_breaker_{func.__name__}",
            fallback_function=fallback_function
        )
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                CIRCUIT_BREAKER_FAILURES.labels(
                    service=func.__module__,
                    operation=func.__name__
                ).inc()
                logger.error(f"Circuit breaker caught error in {func.__name__}: {str(e)}")
                raise

        return wrapper
    return circuit_decorator 