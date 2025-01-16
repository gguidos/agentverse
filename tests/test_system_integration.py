"""
System integration tests
"""

import pytest
from typing import List

from src.core.agentverse.message_bus import InMemoryMessageBus
from src.core.agentverse.message import Message, MessageType, MessageRole
from src.core.agentverse.agents import BaseAgent
from src.core.agentverse.agents.user import UserAgent
from src.core.agentverse.exceptions import MessageBusError
from src.core.agentverse.testing.mocks import MockLLM

@pytest.fixture
async def llm_service():
    """Create mock LLM service"""
    return MockLLM()

@pytest.fixture
async def message_bus():
    """Create message bus for testing"""
    bus = InMemoryMessageBus()
    yield bus

@pytest.fixture
async def test_agents(llm_service) -> List[BaseAgent]:
    """Create test agents"""
    agents = [
        UserAgent(
            name="test_user_1",
            user_id="user1",
            llm_service=llm_service
        ),
        UserAgent(
            name="test_user_2", 
            user_id="user2",
            llm_service=llm_service
        )
    ]
    return agents

async def test_basic_system_setup(message_bus, test_agents):
    """Test basic system setup and message flow"""
    
    # Subscribe agents to topics
    topic = "test_topic"
    for agent in test_agents:
        await message_bus.subscribe(topic, agent.name)
    
    # Verify subscriptions
    subscribers = await message_bus.get_subscribers(topic)
    assert len(subscribers) == len(test_agents)
    
    # Test message publishing
    test_message = Message(
        content="Test message",
        type=MessageType.SYSTEM,
        role=MessageRole.SYSTEM,
        sender_id="system",
        receiver_id="all"
    )
    
    await message_bus.publish(topic, test_message)
    
    # Verify message was stored
    topics = await message_bus.get_topics()
    assert topic in topics
    
    # Test unsubscribe
    await message_bus.unsubscribe(topic, test_agents[0].name)
    subscribers = await message_bus.get_subscribers(topic)
    assert len(subscribers) == len(test_agents) - 1

@pytest.mark.asyncio
async def test_message_bus_errors(message_bus):
    """Test message bus error handling"""
    
    # Test invalid topic subscription
    with pytest.raises(MessageBusError):
        await message_bus.subscribe(None, "test_agent")
    
    # Test invalid message publishing
    with pytest.raises(MessageBusError):
        await message_bus.publish("topic", None) 