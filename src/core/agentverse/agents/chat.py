from typing import Dict, Any, Optional, List
import logging

from src.core.agentverse.agents import BaseAgent, AgentConfig
from src.core.agentverse.agents.mixins.message_handler import MessageHandlerMixin
from src.core.agentverse.message_bus import BaseMessageBus
from src.core.agentverse.agents.mixins.memory_handler import MemoryHandlerMixin
from src.core.agentverse.message import Message, MessageType
from src.core.agentverse.memory import BaseMemory
from src.core.agentverse.registry import agent_registry
logger = logging.getLogger(__name__)

@agent_registry.register("chat")
class ChatAgent(BaseAgent, MessageHandlerMixin, MemoryHandlerMixin):
    """Chat agent with message and memory handling"""
    name = "chat"
    description = "General purpose chat agent"
    version = "1.0.0"
    default_capabilities = []

    def __init__(
        self,
        config: AgentConfig,
        message_bus: Optional[BaseMessageBus] = None,
        memory: Optional[BaseMemory] = None
    ):
        """Initialize chat agent
        
        Args:
            config: Agent configuration
            message_bus: Optional message bus
            memory: Optional memory backend
        """
        BaseAgent.__init__(self, config, message_bus, memory)
        MessageHandlerMixin.__init__(self)
        MemoryHandlerMixin.__init__(self, memory)
        
        # Register handlers
        self.register_handler(MessageType.CHAT, self.handle_chat)
        self.register_handler(MessageType.COMMAND, self.handle_command)
    
    async def handle_chat(self, message: Message) -> None:
        """Handle chat message
        
        Args:
            message: Chat message
        """
        try:
            # Store message in memory
            await self.remember(message)
            
            # Get conversation context
            context = await self.get_context(
                filter_dict={
                    "conversation_id": message.metadata.get("conversation_id")
                }
            )
            
            # Generate response with context
            response = await self.generate_response(
                message,
                context=context
            )
            
            # Create response message
            response_msg = Message(
                content=response,
                type=MessageType.CHAT,
                sender=self.name,
                receiver={"all"},
                metadata={
                    "conversation_id": message.metadata.get("conversation_id"),
                    "parent_id": message.id
                }
            )
            
            # Store response
            await self.remember(response_msg)
            
            # Send response
            await self.send_message(response_msg)
            
        except Exception as e:
            logger.error(f"Chat handling failed: {str(e)}")
    
    async def handle_command(self, message: Message) -> None:
        """Handle command message
        
        Args:
            message: Command message
        """
        # Process command
        if message.content == "clear":
            await self.clear_context()
        elif message.content == "reset":
            await self.reset()
    
    async def generate_response(
        self,
        message: Message,
        context: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Generate response to chat message
        
        Args:
            message: Input message
            context: Optional conversation context
            
        Returns:
            Generated response
        """
        # Implement response generation using context
        raise NotImplementedError
    
    async def search_memory(
        self,
        query: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Search agent memory
        
        Args:
            query: Search query
            **kwargs: Search options
            
        Returns:
            Search results
        """
        return await self.recall(query, **kwargs)
    
    async def clear_memory(self) -> None:
        """Clear agent memory"""
        await self.clear_context()
    
    async def reset(self) -> None:
        """Reset agent state"""
        await self.clear_memory() 