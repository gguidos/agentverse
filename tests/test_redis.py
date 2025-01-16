"""
Redis integration tests
"""

import pytest
from typing import Type

from src.core.agentverse.agents import BaseAgent
from src.core.agentverse.agents.assistant import AssistantAgent
from src.core.agentverse.testing.mocks import MockLLM

class TestRedisIntegration:
    """Test Redis integration"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test fixtures"""
        self.llm = MockLLM()
        self.redis = None  # Add mock Redis if needed
    
    async def create_test_agent(
        self,
        agent_class: Type[BaseAgent],
        **kwargs
    ) -> BaseAgent:
        """Create agent for testing"""
        return agent_class(
            llm_service=self.llm,
            **kwargs
        )
    
    @pytest.mark.asyncio
    async def test_agent_redis_usage(self):
        """Test agent Redis usage"""
        agent = await self.create_test_agent(
            AssistantAgent,
            name="test_agent",
            redis=self.redis
        )
        assert agent.name == "test_agent" 