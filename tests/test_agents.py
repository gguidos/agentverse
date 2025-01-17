"""
Agent tests
"""

import pytest
from typing import Type
from datetime import datetime

from src.core.agentverse.agents import BaseAgent
from src.core.agentverse.agents.assistant import AssistantAgent
from src.core.agentverse.message import Message, MessageType, MessageRole
from src.core.agentverse.testing.mocks.llm import MockLLM, MockLLMConfig

class TestAssistantAgent:
    """Test assistant agent implementation"""
    
    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test fixtures"""
        self.llm = MockLLM(
            responses=["Hello!", "How can I help?"],
            config=MockLLMConfig(model="mock-llm")
        )
        self.memory = None  # Add mock memory if needed
    
    async def create_test_agent(
        self,
        agent_class: Type[BaseAgent],
        **kwargs
    ) -> BaseAgent:
        """Create agent for testing"""
        agent = agent_class(**kwargs)
        agent.llm = self.llm
        return agent
    
    @pytest.mark.asyncio
    async def test_basic_response(self):
        """Test basic message response"""
        agent = await self.create_test_agent(
            AssistantAgent,
            name="test_assistant"
        )
        
        message = Message.user(content="Hello")
        response = await agent.process_message(message)
        
        assert response.content == "Hello!"
        assert response.type == MessageType.ASSISTANT
        assert response.role == MessageRole.ASSISTANT
        assert response.sender_id == "test_assistant"
    
    @pytest.mark.asyncio
    async def test_memory_storage(self):
        """Test message memory storage"""
        agent = await self.create_test_agent(
            AssistantAgent,
            name="test_memory_agent"
        )
        
        message = Message.user(content="Test message")
        await agent.process_message(message)
        
        assert len(agent.message_history) == 2  # Input + response
        assert agent.message_history[0].content == "Test message"
        assert agent.message_history[1].content == "Hello!"

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