import pytest
import asyncio
from src.core.agentverse.resources import (
    RateLimiter,
    ResourceManager,
    ResourceQuota
)

@pytest.mark.asyncio
async def test_rate_limiter():
    # Create rate limiter
    limiter = RateLimiter(
        name="test",
        rate=10,  # 10 requests per minute
        burst=2
    )
    
    # Test burst capacity
    assert await limiter.acquire()  # Should succeed
    assert await limiter.acquire()  # Should succeed
    assert not await limiter.acquire()  # Should fail
    
    # Test rate limiting
    await asyncio.sleep(6)  # Wait for token replenishment
    assert await limiter.acquire()  # Should succeed

@pytest.mark.asyncio
async def test_resource_quota():
    manager = ResourceManager()
    
    # Add quota
    manager.add_quota(
        "memory",
        max_usage=100,
        unit="MB"
    )
    
    # Test usage
    assert await manager.check_quota("memory", 50)  # Should allow
    assert await manager.check_quota("memory", 40)  # Should allow
    assert not await manager.check_quota("memory", 20)  # Should deny 