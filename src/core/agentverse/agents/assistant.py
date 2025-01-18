"""Assistant agent implementation"""

from typing import Dict, Any
from src.core.agentverse.agents.base import BaseAgent
from src.core.agentverse.entities.agent import AgentConfig
from src.core.agentverse.registry import agent_registry

@agent_registry.register("assistant")
class AssistantAgent(BaseAgent):
    """Assistant agent implementation"""
    name = "assistant"
    description = "General purpose assistant agent"
    version = "1.0.0"
    default_capabilities = []
    
    def __init__(self, config: AgentConfig, llm: Any):
        super().__init__(config)
        self.llm = llm

    async def process_message(self, message: str) -> str:
        """Process incoming message"""
        return await self.llm.generate(message) 