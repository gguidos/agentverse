from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
import asyncio
import logging

from src.core.agentverse.message import (
    BaseMessage,
    ChatMessage,
    CommandMessage,
    EventMessage
)
from src.core.agentverse.message_bus import BaseMessageBus
from src.core.agentverse.memory import BaseMemory

logger = logging.getLogger(__name__)

class AgentConfig(BaseModel):
    """Agent configuration"""
    name: str
    description: Optional[str] = None
    bus_config: Optional[Dict[str, Any]] = None
    memory_config: Optional[Dict[str, Any]] = None
    subscriptions: List[str] = Field(default_factory=list)

class BaseAgent:
    """Base agent class with message bus support"""
    
    def __init__(
        self,
        config: AgentConfig,
        message_bus: Optional[BaseMessageBus] = None,
        memory: Optional[BaseMemory] = None
    ):
        """Initialize agent
        
        Args:
            config: Agent configuration
            message_bus: Optional message bus
            memory: Optional memory backend
        """
        self.config = config
        self.message_bus = message_bus
        self.memory = memory
        self._running = False
        self._tasks = set()
    
    async def start(self) -> None:
        """Start agent"""
        if self._running:
            return
            
        self._running = True
        
        # Connect to message bus
        if self.message_bus:
            await self.message_bus.connect()
            
            # Subscribe to topics
            for topic in self.config.subscriptions:
                await self.message_bus.subscribe(
                    topic,
                    self.handle_message
                )
        
        # Start processing loop
        self._tasks.add(
            asyncio.create_task(self._process_loop())
        )
        
        logger.info(f"Agent {self.config.name} started")
    
    async def stop(self) -> None:
        """Stop agent"""
        self._running = False
        
        # Cancel tasks
        for task in self._tasks:
            task.cancel()
        
        # Disconnect from message bus
        if self.message_bus:
            await self.message_bus.disconnect()
            
        logger.info(f"Agent {self.config.name} stopped")
    
    async def send_message(
        self,
        message: Union[BaseMessage, Dict[str, Any]],
        topic: Optional[str] = None
    ) -> None:
        """Send message
        
        Args:
            message: Message to send
            topic: Optional topic override
        """
        if not self.message_bus:
            logger.warning("No message bus configured")
            return
            
        if isinstance(message, dict):
            message = BaseMessage(**message)
            
        # Set source if not set
        if not message.metadata.source:
            message.metadata.source = self.config.name
            
        # Publish message
        await self.message_bus.publish(
            topic or f"agent.{self.config.name}",
            message.dict()
        )
    
    async def handle_message(
        self,
        message: Dict[str, Any]
    ) -> None:
        """Handle incoming message
        
        Args:
            message: Message data
        """
        try:
            # Convert to message object
            if isinstance(message, dict):
                message_type = message.get("type", "chat")
                message = BaseMessage.create(message_type, **message)
            
            # Handle different message types
            if isinstance(message, ChatMessage):
                await self.handle_chat(message)
            elif isinstance(message, CommandMessage):
                await self.handle_command(message)
            elif isinstance(message, EventMessage):
                await self.handle_event(message)
            else:
                await self.handle_other(message)
                
        except Exception as e:
            logger.error(f"Message handling failed: {str(e)}")
    
    async def handle_chat(self, message: ChatMessage) -> None:
        """Handle chat message
        
        Args:
            message: Chat message
        """
        pass
    
    async def handle_command(self, message: CommandMessage) -> None:
        """Handle command message
        
        Args:
            message: Command message
        """
        pass
    
    async def handle_event(self, message: EventMessage) -> None:
        """Handle event message
        
        Args:
            message: Event message
        """
        pass
    
    async def handle_other(self, message: BaseMessage) -> None:
        """Handle other message types
        
        Args:
            message: Message object
        """
        pass
    
    async def _process_loop(self) -> None:
        """Main processing loop"""
        while self._running:
            try:
                # Process agent logic
                await self.process()
                
                # Small delay to prevent busy loop
                await asyncio.sleep(0.1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Processing error: {str(e)}")
                await asyncio.sleep(1)
    
    async def process(self) -> None:
        """Process agent logic
        
        Override this method to implement agent behavior
        """
        pass 