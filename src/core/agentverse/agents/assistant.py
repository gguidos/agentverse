"""
Assistant agent implementation
"""

from typing import Any, Dict, Optional

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.message import Message, MessageType, MessageRole
from src.core.agentverse.exceptions import AgentError

class AssistantAgent(BaseAgent):
    """AI Assistant agent implementation"""
    
    async def process_message(self, message: Message) -> Message:
        """Process incoming message
        
        Args:
            message: Input message
            
        Returns:
            Response message
            
        Raises:
            AgentError: If processing fails
        """
        try:
            if not self.llm:
                raise AgentError("LLM service not configured")
            
            # Store input message in history
            self.message_history.append(message)
                
            # Generate response using LLM
            response_text = await self.llm.generate_response(message.content)
            
            # Create response message
            response = Message(
                content=response_text,
                type=MessageType.ASSISTANT,
                role=MessageRole.ASSISTANT,
                sender_id=self.name,
                receiver_id=message.sender_id,
                parent_id=message.id
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