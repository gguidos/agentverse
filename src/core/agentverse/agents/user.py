"""User agent implementation"""

from typing import Dict, Any
from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.llms import BaseLLM
from src.core.agentverse.registry import agent_registry
from src.core.agentverse.message import Message

@agent_registry.register("user")
class UserAgent(BaseAgent):
    """User agent implementation"""
    
    def __init__(self, config: Dict[str, Any], llm: BaseLLM):
        super().__init__(name=config.get("name", "user"), llm=llm)
        self.user_id = config.get("user_id")

    async def process_message(self, message: Message) -> Message:
        """Process incoming message
        
        Args:
            message: Input message
            
        Returns:
            Response message
        """
        response = await self.llm.generate(message.content)
        return Message(
            content=response,
            sender=self.name,
            receiver={"all"},
            metadata={
                "user_id": self.user_id
            }
        ) 