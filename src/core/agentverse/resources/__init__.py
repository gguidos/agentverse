"""
AgentVerse Resource Management Module

This module provides rate limiting and resource management capabilities.
It helps control and monitor resource usage across the system.

Key Components:
    - RateLimiter: Token bucket rate limiting
    - ResourceManager: Resource allocation and tracking
    - ResourcePool: Shared resource management
    - Quotas: Usage quotas and limits

Example Usage:
    >>> from src.core.agentverse.resources import RateLimiter, ResourceManager
    >>> 
    >>> # Configure rate limits
    >>> llm_limiter = RateLimiter(
    ...     name="llm_calls",
    ...     rate=100,  # requests per minute
    ...     burst=20   # burst capacity
    ... )
    >>> 
    >>> # Use rate limiter
    >>> async with llm_limiter:
    ...     response = await llm_service.generate(prompt)
"""

from typing import Dict, Any, Optional, List, Union
import asyncio
import time
import logging
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class RateLimitConfig(BaseModel):
    """Configuration for rate limiting"""
    rate: float  # Requests per minute
    burst: int = 1  # Burst capacity
    window: float = 60.0  # Time window in seconds
    
class ResourceQuota(BaseModel):
    """Resource quota configuration"""
    max_usage: float
    current_usage: float = 0
    unit: str = ""
    reset_interval: Optional[float] = None
    last_reset: datetime = Field(default_factory=datetime.utcnow)

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(
        self,
        name: str,
        rate: float,
        burst: int = 1,
        window: float = 60.0
    ):
        """Initialize rate limiter
        
        Args:
            name: Limiter name
            rate: Requests per minute
            burst: Burst capacity
            window: Time window in seconds
        """
        self.name = name
        self.config = RateLimitConfig(
            rate=rate,
            burst=burst,
            window=window
        )
        self.tokens = burst
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
        logger.debug(f"Initialized rate limiter '{name}'")
    
    async def acquire(self) -> bool:
        """Acquire rate limit token
        
        Returns:
            Whether token was acquired
        """
        async with self._lock:
            now = time.monotonic()
            time_passed = now - self.last_update
            self.last_update = now
            
            # Add new tokens based on time passed
            self.tokens = min(
                self.config.burst,
                self.tokens + time_passed * (self.config.rate / self.config.window)
            )
            
            if self.tokens >= 1:
                self.tokens -= 1
                logger.debug(f"Rate limiter '{self.name}': token acquired ({self.tokens} remaining)")
                return True
            
            logger.warning(f"Rate limiter '{self.name}': no tokens available")
            return False
    
    async def __aenter__(self) -> None:
        """Async context manager entry"""
        while not await self.acquire():
            delay = 1.0 / self.config.rate
            logger.debug(f"Rate limiter '{self.name}': waiting {delay:.2f}s")
            await asyncio.sleep(delay)
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit"""
        pass

class ResourceManager:
    """Manages system resources and rate limits"""
    
    def __init__(self):
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.quotas: Dict[str, ResourceQuota] = {}
        logger.info("Initialized ResourceManager")
    
    def add_rate_limiter(
        self,
        name: str,
        rate: float,
        burst: int = 1,
        window: float = 60.0
    ) -> RateLimiter:
        """Add rate limiter
        
        Args:
            name: Limiter name
            rate: Requests per minute
            burst: Burst capacity
            window: Time window in seconds
            
        Returns:
            Created rate limiter
        """
        limiter = RateLimiter(
            name=name,
            rate=rate,
            burst=burst,
            window=window
        )
        self.rate_limiters[name] = limiter
        logger.debug(f"Added rate limiter '{name}' (rate={rate}/min, burst={burst})")
        return limiter
    
    def add_quota(
        self,
        name: str,
        max_usage: float,
        unit: str = "",
        reset_interval: Optional[float] = None
    ) -> ResourceQuota:
        """Add resource quota
        
        Args:
            name: Quota name
            max_usage: Maximum allowed usage
            unit: Usage unit
            reset_interval: Optional reset interval in seconds
            
        Returns:
            Created quota
        """
        quota = ResourceQuota(
            max_usage=max_usage,
            unit=unit,
            reset_interval=reset_interval
        )
        self.quotas[name] = quota
        logger.debug(f"Added quota '{name}' (max={max_usage}{unit}, reset={reset_interval}s)")
        return quota
    
    async def check_quota(self, name: str, usage: float) -> bool:
        """Check if usage is within quota
        
        Args:
            name: Quota name
            usage: Requested usage amount
            
        Returns:
            Whether usage is allowed
        """
        if name not in self.quotas:
            logger.warning(f"No quota defined for '{name}'")
            return True
            
        quota = self.quotas[name]
        
        # Check reset interval
        if quota.reset_interval:
            now = datetime.utcnow()
            if (now - quota.last_reset).total_seconds() >= quota.reset_interval:
                logger.info(f"Resetting quota '{name}' (interval elapsed)")
                quota.current_usage = 0
                quota.last_reset = now
        
        # Check usage
        if quota.current_usage + usage > quota.max_usage:
            logger.warning(
                f"Quota exceeded for '{name}': "
                f"current={quota.current_usage}, "
                f"requested={usage}, "
                f"max={quota.max_usage}"
            )
            return False
            
        quota.current_usage += usage
        logger.debug(
            f"Updated quota '{name}': "
            f"current={quota.current_usage}, "
            f"remaining={quota.max_usage - quota.current_usage}"
        )
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get resource metrics
        
        Returns:
            Resource usage metrics
        """
        return {
            "rate_limits": {
                name: {
                    "rate": limiter.config.rate,
                    "burst": limiter.config.burst,
                    "tokens": limiter.tokens
                }
                for name, limiter in self.rate_limiters.items()
            },
            "quotas": {
                name: {
                    "max": quota.max_usage,
                    "current": quota.current_usage,
                    "unit": quota.unit
                }
                for name, quota in self.quotas.items()
            }
        }

__all__ = [
    "RateLimiter",
    "ResourceManager",
    "RateLimitConfig",
    "ResourceQuota"
] 