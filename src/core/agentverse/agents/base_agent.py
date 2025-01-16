"""
Base agent class for AgentVerse
"""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from src.core.agentverse.message import Message, MessageType, MessageRole
from src.core.agentverse.services.llm.base import BaseLLMService
from src.core.agentverse.memory.base import BaseMemory
from src.core.agentverse.exceptions import AgentError, AgentStateError

class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(
        self,
        name: str,
        llm_service: BaseLLMService,
        memory: Optional[BaseMemory] = None,
        **kwargs
    ):
        """Initialize agent
        
        Args:
            name: Agent name
            llm_service: LLM service instance
            memory: Optional memory instance
            **kwargs: Additional agent arguments
        """
        self.name = name
        self.llm_service = llm_service
        self.memory = memory
        self.state: Dict[str, Any] = {}
        self.message_history: List[Message] = []
    
    @abstractmethod
    async def process_message(self, message: Message) -> Message:
        """Process incoming message
        
        Args:
            message: Input message
            
        Returns:
            Response message
            
        Raises:
            AgentError: If processing fails
        """
        pass
    
    async def send_message(self, content: str, **kwargs) -> Message:
        """Send message from agent
        
        Args:
            content: Message content
            **kwargs: Additional message arguments
            
        Returns:
            Created message
        """
        message = Message.assistant(
            content=content,
            sender_id=self.name,
            **kwargs
        )
        self.message_history.append(message)
        return message
    
    async def receive_message(self, message: Message) -> Message:
        """Receive and process message
        
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
            
            # Process message
            response = await self.process_message(message)
            
            # Store response
            self.message_history.append(response)
            
            return response
            
        except Exception as e:
            raise AgentError(
                message=f"Failed to process message: {str(e)}",
                details={
                    "agent": self.name,
                    "message_id": message.id
                }
            )
    
    async def get_state(self, key: str) -> Any:
        """Get agent state value
        
        Args:
            key: State key
            
        Returns:
            State value
            
        Raises:
            AgentStateError: If key not found
        """
        if key not in self.state:
            raise AgentStateError(f"State key not found: {key}")
        return self.state[key]
    
    async def set_state(self, key: str, value: Any) -> None:
        """Set agent state value
        
        Args:
            key: State key
            value: State value
        """
        self.state[key] = value
    
    async def reset(self) -> None:
        """Reset agent state"""
        self.state.clear()
        self.message_history.clear()
        if self.memory:
            await self.memory.clear()
    
    def get_message_history(self) -> List[Message]:
        """Get message history
        
        Returns:
            List of messages
        """
        return self.message_history.copy() 