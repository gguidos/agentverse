"""Mock Agent Module"""

from typing import Optional, List
from datetime import datetime

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.message import Message, MessageType, MessageRole
from src.core.agentverse.testing.mocks.llm import MockLLM

class MockAgent(BaseAgent):
    """Mock agent for testing"""
    
    def __init__(self, name: str, responses: Optional[List[str]] = None):
        super().__init__(name=name, llm=MockLLM(responses=responses))
    
    async def process_message(self, message: Message) -> Message:
        """Process message with mock response"""
        response = await self.llm.generate_response(message.content)
        return Message(
            content=response.content,
            type=MessageType.ASSISTANT,
            role=MessageRole.ASSISTANT,
            sender_id=self.name,
            receiver_id=message.sender_id,
            parent_id=message.id
        ) 