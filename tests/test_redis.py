import pytest
from src.core.agentverse.testing import MockRedis, AgentTestCase

@pytest.mark.asyncio
async def test_mock_redis_basic():
    """Test basic Redis operations"""
    redis = MockRedis()
    
    # Test connection
    await redis.connect()
    assert redis._connected
    
    # Test set/get
    await redis.set("test_key", "test_value")
    value = await redis.get("test_key")
    assert value == "test_value"
    
    # Test delete
    await redis.delete("test_key")
    value = await redis.get("test_key")
    assert value is None
    
    # Test call tracking
    assert redis.get_call_count("set") == 1
    assert redis.get_call_count("get") == 2
    assert redis.get_call_count("delete") == 1

class TestRedisIntegration(AgentTestCase):
    """Test Redis integration with agents"""
    
    @pytest.mark.asyncio
    async def test_agent_redis_usage(self):
        agent = await self.create_test_agent(
            SomeAgent,
            redis=self.redis
        )
        
        # Test Redis operations
        await agent.some_redis_operation()
        
        # Verify Redis calls
        self.assert_redis_operation(
            "set",
            key="some_key",
            value="some_value",
            times=1
        ) 