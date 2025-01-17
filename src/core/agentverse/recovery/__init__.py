"""
Recovery mechanisms
"""

import logging
from typing import TypeVar, Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryHandler:
    """Retry handler for async operations"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
    
    async def handle(self, operation: Callable[..., T], *args, **kwargs) -> T:
        """Handle retries for operation"""
        attempts = 0
        last_error = None
        
        while attempts < self.max_retries:
            try:
                attempts += 1
                return await operation(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempts} failed: {str(e)}")
        
        if last_error:
            raise last_error
        raise RuntimeError("All retry attempts failed")

class CircuitBreaker:
    """Circuit breaker for async operations"""
    
    def __init__(self, failure_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.failure_count = 0
        self.is_open = False
    
    async def execute(self, operation: Callable[..., T], *args, **kwargs) -> T:
        """Execute operation with circuit breaker"""
        if self.is_open:
            logger.error("Circuit open - too many failures")
            raise RuntimeError("Circuit breaker open")
        
        try:
            result = await operation(*args, **kwargs)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
            raise e

def circuit_breaker(failure_threshold: int = 3):
    """Circuit breaker decorator"""
    breaker = CircuitBreaker(failure_threshold=failure_threshold)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await breaker.execute(func, *args, **kwargs)
        return wrapper
    return decorator

__all__ = [
    "RetryHandler",
    "CircuitBreaker",
    "circuit_breaker"
] 