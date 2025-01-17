"""Assistant agent implementation"""

from typing import Dict, Any
from src.core.agentverse.agents.base import BaseAgent
from src.core.agentverse.llms import BaseLLM

class AssistantAgent(BaseAgent):
    """AI Assistant agent"""
    
    def __init__(self, config: Dict[str, Any], llm: BaseLLM):
        super().__init__(config, llm)
        self.name = config.get("name", "assistant")

    async def process_message(self, message: str) -> str:
        """Process incoming message"""
        return await self.llm.generate(message) 