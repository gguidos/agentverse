"""User Agent Module"""

from typing import Optional
from datetime import datetime

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.message import Message, MessageType, MessageRole
from src.core.agentverse.exceptions import AgentError
from src.core.agentverse.llm.base import LLMResult

class UserAgent(BaseAgent):
    """User agent implementation"""
    
    def __init__(
        self,
        name: str,
        user_id: str,
        llm: Optional['BaseLLM'] = None
    ):
        super().__init__(name=name, llm=llm)
        self.user_id = user_id
    
    async def process_message(self, message: Message) -> Message:
        """Process incoming message"""
        try:
            if not self.llm:
                raise AgentError("LLM service not configured")
            
            # Store input message in history
            self.message_history.append(message)
            
            # Generate response using LLM
            llm_response = await self.llm.generate_response(message.content)
            response_text = llm_response.content if isinstance(llm_response, LLMResult) else str(llm_response)
            
            # Create response message
            response = Message(
                content=response_text,
                type=MessageType.USER,
                role=MessageRole.USER,
                sender_id=self.name,
                receiver_id=message.sender_id,
                parent_id=message.id,
                metadata={"user_id": self.user_id}
            )
            
            # Store response in history
            self.message_history.append(response)
            
            return response
            
        except Exception as e:
            raise AgentError(
                message="Failed to process message",
                details={
                    "agent": self.name,
                    "error": str(e)
                }
            ) 