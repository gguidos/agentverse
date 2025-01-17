"""
Resource management module
"""

import logging
import asyncio
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class QuotaExceededError(Exception):
    """Raised when resource quota is exceeded"""
    pass

class ResourceQuota(BaseModel):
    """Resource quota"""
    current: float = Field(default=0)
    max: float = Field(default=100)
    unit: str = Field(default="units")
    
    def allocate_memory(self, amount: float) -> None:
        """Allocate memory"""
        if self.current + amount > self.max:
            logger.warning(f"Quota exceeded for 'memory': current={self.current}, requested={amount}, max={self.max}")
            raise QuotaExceededError(f"Memory quota exceeded: {self.current + amount} > {self.max}")
        self.current += amount
    
    def release_memory(self, amount: float) -> None:
        """Release memory"""
        self.current = max(0, self.current - amount)

class RateLimiter(BaseModel):
    """Rate limiter configuration"""
    
    tokens: int = Field(default=60, description="Available tokens")
    refill_rate: float = Field(default=1.0, description="Tokens per second")
    max_tokens: int = Field(default=60, description="Maximum token capacity")
    last_refill: float = Field(default_factory=lambda: asyncio.get_event_loop().time())
    burst: int = Field(default=1, description="Maximum burst size")

    model_config = {
        "arbitrary_types_allowed": True,
        "ser_json_timedelta": "iso8601",
        "json_schema_extra": {
            "examples": [{
                "tokens": 60,
                "refill_rate": 1.0,
                "max_tokens": 60,
                "burst": 1
            }]
        }
    }

    @classmethod
    def from_rate(cls, rate: float, burst: int = 1) -> "RateLimiter":
        """Create rate limiter from rate specification
        
        Args:
            rate: Tokens per second
            burst: Maximum burst size
            
        Returns:
            Configured rate limiter
        """
        return cls(
            tokens=burst,
            refill_rate=rate,
            max_tokens=burst,
            burst=burst
        )

    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens from the limiter
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            Whether tokens were acquired successfully
        """
        # Refill tokens
        now = asyncio.get_event_loop().time()
        elapsed = now - self.last_refill
        new_tokens = int(elapsed * self.refill_rate)
        
        if new_tokens > 0:
            self.tokens = min(
                self.tokens + new_tokens,
                self.max_tokens
            )
            self.last_refill = now
        
        # Check against burst limit
        if tokens > self.burst:
            return False
        
        # Check available tokens
        if self.tokens < tokens:
            return False
            
        self.tokens -= tokens
        return True

class ResourceManager:
    """Manages system resources and limits"""
    
    def __init__(self):
        self.quotas: Dict[str, ResourceQuota] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        logger.info("Initialized ResourceManager")
    
    async def add_quota(self, name: str, max_value: float, unit: str = "units") -> None:
        """Add resource quota
        
        Args:
            name: Quota name
            max_value: Maximum allowed value
            unit: Unit of measurement
        """
        self.quotas[name] = ResourceQuota(max=max_value, unit=unit)
    
    async def add_rate_limiter(
        self,
        name: str,
        tokens: int = 60,
        refill_rate: float = 1.0
    ) -> None:
        """Add rate limiter"""
        self.rate_limiters[name] = RateLimiter(
            tokens=tokens,
            refill_rate=refill_rate,
            max_tokens=tokens
        )
    
    async def check_quota(self, name: str, amount: float) -> bool:
        """Check if quota allows operation"""
        if name not in self.quotas:
            return True
            
        quota = self.quotas[name]
        if quota.current + amount > quota.max:
            logger.warning(
                f"Quota exceeded for '{name}': current={quota.current}, "
                f"requested={amount}, max={quota.max}"
            )
            return False
            
        return True
    
    async def consume_quota(self, name: str, amount: float) -> None:
        """Consume quota amount"""
        if name in self.quotas:
            self.quotas[name].current += amount
    
    async def check_rate_limit(self, name: str, tokens: int = 1) -> bool:
        """Check if rate limit allows operation"""
        if name not in self.rate_limiters:
            return True
            
        limiter = self.rate_limiters[name]
        
        # Refill tokens
        now = asyncio.get_event_loop().time()
        elapsed = now - limiter.last_refill
        new_tokens = int(elapsed * limiter.refill_rate)
        
        if new_tokens > 0:
            limiter.tokens = min(
                limiter.tokens + new_tokens,
                limiter.max_tokens
            )
            limiter.last_refill = now
        
        if limiter.tokens < tokens:
            logger.warning(f"Rate limiter '{name}': no tokens available")
            return False
            
        limiter.tokens -= tokens
        return True

__all__ = [
    "ResourceManager",
    "ResourceQuota",
    "RateLimiter"
] 