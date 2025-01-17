"""User agent implementation"""

from typing import Dict, Any
from src.core.agentverse.agents.base import BaseAgent
from src.core.agentverse.llms import BaseLLM

class UserAgent(BaseAgent):
    """User agent implementation"""
    
    def __init__(self, config: Dict[str, Any], llm: BaseLLM):
        super().__init__(config, llm)
        self.name = config.get("name", "user")
        self.user_id = config.get("user_id")

    async def process_message(self, message: str) -> str:
        """Process incoming message"""
        return await self.llm.generate(message) 