import pytest
import asyncio
from src.core.agentverse.resources import (
    RateLimiter,
    ResourceManager,
    ResourceQuota
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
async def test_resource_quota():
    manager = ResourceManager()
    
    # Add quota
    await manager.add_quota(
        "memory",
        max_value=100,
        unit="MB"
    )
    
    # Test quota check
    assert await manager.check_quota("memory", 20)  # Should succeed
    await manager.consume_quota("memory", 90)
    assert not await manager.check_quota("memory", 20)  # Should fail 