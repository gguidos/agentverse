"""
Agent tests
"""

import pytest
from typing import Type

from src.core.agentverse.agents import BaseAgent
from src.core.agentverse.agents.assistant import AssistantAgent
from src.core.agentverse.message import Message
from src.core.agentverse.testing.mocks import MockLLM

class TestAssistantAgent:
    """Test assistant agent implementation"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test fixtures"""
        self.llm = MockLLM()
        self.memory = None  # Add mock memory if needed
    
    async def test_basic_response(self):
        """Test basic message response"""
        agent = await self.create_test_agent(
            AssistantAgent,
            name="test_assistant"
        )
        
        message = Message.user(content="Hello")
        response = await agent.process_message(message)
        
        assert response.content == "Mock response"
    
    async def test_memory_storage(self):
        """Test message memory storage"""
        agent = await self.create_test_agent(
            AssistantAgent,
            name="test_memory_agent"
        )
        
        message = Message.user(content="Test message")
        await agent.process_message(message)
        
        history = agent.get_message_history()
        assert len(history) == 2  # Input + response
    
    async def create_test_agent(
        self,
        agent_class: Type[BaseAgent],
        **kwargs
    ) -> BaseAgent:
        """Create agent for testing"""
        return agent_class(
            llm_service=self.llm,
            memory=self.memory,
            **kwargs
        )

@pytest.mark.asyncio
async def test_agent_creation():
    """Test agent creation"""
    llm = MockLLM()
    agent = AssistantAgent(
        name="test",
        llm_service=llm
    )
    assert agent.name == "test"
    assert agent.llm == llm 