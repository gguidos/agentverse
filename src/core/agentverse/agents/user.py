"""
User agent implementation
"""

import logging
from typing import Any, Dict, Optional

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.message import Message, MessageType, MessageRole
from src.core.agentverse.exceptions import AgentError

logger = logging.getLogger(__name__)

class UserAgent(BaseAgent):
    """Agent representing a human user"""
    
    def __init__(
        self,
        name: str,
        user_id: str,
        preferences: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize user agent
        
        Args:
            name: Agent name
            user_id: User identifier
            preferences: Optional user preferences
            **kwargs: Additional arguments
        """
        super().__init__(name=name, **kwargs)
        self.user_id = user_id
        self.preferences = preferences or {}
    
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
            # Store message in history
            self.message_history.append(message)
            
            # Create response message
            response = Message(
                content="",  # Empty content as user needs to provide input
                type=MessageType.USER,
                role=MessageRole.USER,
                sender_id=self.user_id,
                receiver_id=message.sender_id,
                parent_id=message.id,
                metadata={
                    "preferences": self.preferences,
                    "requires_input": True
                }
            )
            
            # Store response
            self.message_history.append(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            raise AgentError(
                message="Message processing failed",
                details={
                    "agent": self.name,
                    "error": str(e)
                }
            )
    
    async def get_preferences(self) -> Dict[str, Any]:
        """Get user preferences
        
        Returns:
            User preferences dictionary
        """
        return self.preferences.copy()
    
    async def update_preferences(self, updates: Dict[str, Any]) -> None:
        """Update user preferences
        
        Args:
            updates: Preference updates
        """
        self.preferences.update(updates)
        logger.info(f"Updated preferences for user {self.user_id}") 