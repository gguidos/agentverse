"""Assistant agent implementation"""

from typing import Dict, Any
from src.core.agentverse.agents.base import BaseAgent
from src.core.agentverse.entities.agent import AgentConfig

class AssistantAgent(BaseAgent):
    """Assistant agent implementation"""
    
    def __init__(self, config: AgentConfig, llm: Any):
        super().__init__(config)
        self.llm = llm

    async def process_message(self, message: str) -> str:
        """Process incoming message"""
        return await self.llm.generate(message) 