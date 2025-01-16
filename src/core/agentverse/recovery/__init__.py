"""
Recovery mechanisms
"""

import logging
import asyncio
from functools import wraps
from typing import Any, Callable, Optional, Type, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class RetryConfig(BaseModel):
    """Configuration for retry handling"""
    
    max_attempts: int = Field(default=3, description="Maximum retry attempts")
    delay_seconds: float = Field(default=1.0, description="Initial delay between retries")
    backoff_factor: float = Field(default=2.0, description="Exponential backoff multiplier")
    exceptions: Tuple[Type[Exception], ...] = Field(
        default=(Exception,),
        description="Exceptions to catch and retry"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "max_attempts": 3,
                "delay_seconds": 1.0,
                "backoff_factor": 2.0,
                "exceptions": ["Exception"]
            }]
        }
    }

class RetryHandler:
    """Handles retry logic for operations"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
    
    def handle(self, func: Callable) -> Callable:
        """Decorator for retry handling"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempts = 0
            last_error = None
            delay = self.config.delay_seconds
            
            while attempts < self.config.max_attempts:
                try:
                    return await func(*args, **kwargs)
                except self.config.exceptions as e:
                    attempts += 1
                    last_error = e
                    logger.warning(
                        f"Attempt {attempts} failed: {str(e)}"
                    )
                    if attempts < self.config.max_attempts:
                        await asyncio.sleep(delay)
                        delay *= self.config.backoff_factor
            
            raise last_error
            
        return wrapper

def circuit_breaker(func: Optional[Callable] = None, *, max_failures: int = 3) -> Callable:
    """Circuit breaker decorator"""
    def decorator(func: Callable) -> Callable:
        failures = 0
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal failures
            
            if failures >= max_failures:
                logger.error("Circuit open - too many failures")
                raise RuntimeError("Circuit breaker open")
                
            try:
                result = await func(*args, **kwargs)
                failures = 0  # Reset on success
                return result
            except Exception as e:
                failures += 1
                raise
                
        return wrapper
        
    if func is None:
        return decorator
    return decorator(func)

__all__ = [
    "RetryConfig",
    "RetryHandler",
    "circuit_breaker"
] 