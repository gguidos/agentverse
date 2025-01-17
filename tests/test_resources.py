"""Resource management tests"""

import pytest
import asyncio
import logging
from src.core.agentverse.resources import (
    RateLimiter,
    ResourceQuota,
    QuotaExceededError
)

@pytest.mark.asyncio
async def test_rate_limiter():
    # Create rate limiter with 10 tokens/sec and burst of 2
    limiter = RateLimiter.from_rate(
        rate=10.0,  # 10 tokens per second
        burst=2     # Maximum burst of 2
    )
    
    # Test burst capacity
    assert await limiter.acquire()  # Should succeed (2 -> 1)
    assert await limiter.acquire()  # Should succeed (1 -> 0)
    assert not await limiter.acquire()  # Should fail (0 tokens)
    
    # Test rate limiting
    await asyncio.sleep(0.2)  # Wait for token replenishment (should get 2 tokens)
    assert await limiter.acquire()  # Should succeed

@pytest.mark.asyncio
async def test_resource_quota(caplog):
    """Test resource quota management"""
    quota = ResourceQuota(max_memory=100)
    
    with caplog.at_level(logging.WARNING):
        # Allocate memory
        quota.allocate_memory(90)
        
        # Try to exceed quota
        with pytest.raises(QuotaExceededError):
            quota.allocate_memory(20)
    
    # Verify quota exceeded warning was logged
    assert any("Quota exceeded" in r.message for r in caplog.records) 