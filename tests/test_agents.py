import pytest
from src.core.agentverse.testing import (
    AgentTestCase,
    async_test,
    MockLLMService
)
from src.core.agentverse.agents import AssistantAgent

class TestAssistantAgent(AgentTestCase):
    
    def setUp(self):
        super().setUp()
        self.config.mock_responses = {
            "Hello": "Hi there!",
            "How are you?": "I'm doing well, thanks!"
        }
    
    @async_test
    async def test_basic_response(self):
        # Create test agent
        agent = await self.create_test_agent(
            AssistantAgent,
            name="test_assistant"
        )
        
        # Test response
        response = await agent.process_message("Hello")
        self.assert_agent_response(response, equals="Hi there!")
        
        # Verify LLM was called
        self.assert_llm_called(times=1)
    
    @async_test
    async def test_memory_storage(self):
        agent = await self.create_test_agent(AssistantAgent)
        
        # Process message
        await agent.process_message("How are you?")
        
        # Verify memory storage
        self.assert_memory_operation(
            "store",
            contains="How are you?"
        )

@pytest.mark.asyncio
async def test_agent_creation():
    """Test agent creation with real services"""
    llm = MockLLMService()
    agent = AssistantAgent(llm_service=llm)
    assert agent is not None 