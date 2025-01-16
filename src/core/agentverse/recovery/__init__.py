"""
AgentVerse Recovery Module

This module provides error handling and recovery mechanisms for the AgentVerse system.
It includes retry logic, circuit breakers, fallback strategies, and state recovery.

Key Components:
    - RetryHandler: Configurable retry logic with backoff
    - StateRecovery: Save and restore system state
    - ErrorRegistry: Central error tracking and handling

Example Usage:
    >>> from src.core.agentverse.recovery import RetryHandler
    >>> from src.core.infrastructure.circuit_breaker import circuit_breaker
    >>> 
    >>> # Configure retry logic
    >>> retry = RetryHandler(max_retries=3, backoff_factor=1.5)
    >>> 
    >>> @retry.wrap
    >>> @circuit_breaker
    >>> async def call_llm(prompt: str) -> str:
    ...     return await llm_service.generate(prompt)
"""

from typing import TypeVar, Callable, Any, Optional, Dict, List
import asyncio
import logging
import time
from datetime import datetime
from functools import wraps
from pydantic import BaseModel, Field

from src.core.infrastructure.circuit_breaker import circuit_breaker

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryConfig(BaseModel):
    """Configuration for retry behavior"""
    max_retries: int = 3
    backoff_factor: float = 1.5
    max_delay: float = 60.0
    retry_exceptions: List[type] = Field(default_factory=lambda: [Exception])

class RecoveryState(BaseModel):
    """State tracking for recovery mechanisms"""
    retry_counts: Dict[str, int] = Field(default_factory=dict)
    last_failures: Dict[str, datetime] = Field(default_factory=dict)
    error_counts: Dict[str, int] = Field(default_factory=dict)

class RetryHandler:
    """Handles retry logic with exponential backoff"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.state = RecoveryState()
    
    def wrap(self, func: Callable[..., T]) -> Callable[..., T]:
        """Wrap function with retry logic"""
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            operation_id = f"{func.__module__}.{func.__name__}"
            retry_count = 0
            
            while True:
                try:
                    result = await func(*args, **kwargs)
                    # Reset retry count on success
                    self.state.retry_counts[operation_id] = 0
                    return result
                    
                except tuple(self.config.retry_exceptions) as e:
                    retry_count += 1
                    self.state.retry_counts[operation_id] = retry_count
                    
                    if retry_count >= self.config.max_retries:
                        logger.error(
                            f"Max retries ({self.config.max_retries}) exceeded for {operation_id}"
                        )
                        raise
                    
                    delay = min(
                        self.config.backoff_factor ** (retry_count - 1),
                        self.config.max_delay
                    )
                    
                    logger.warning(
                        f"Retry {retry_count}/{self.config.max_retries} "
                        f"for {operation_id} after {delay}s: {str(e)}"
                    )
                    
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    # Don't retry unhandled exceptions
                    logger.error(f"Unhandled error in {operation_id}: {str(e)}")
                    raise
                    
        return wrapper

class RecoveryError(Exception):
    """Base class for recovery errors"""
    pass

__all__ = [
    "RetryHandler",
    "RetryConfig",
    "RecoveryState",
    "RecoveryError"
] 