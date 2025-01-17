"""Assistant agent implementation"""

from typing import Dict, Any
from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.llms import BaseLLM
from src.core.agentverse.registry import agent_registry

@agent_registry.register("assistant")
class AssistantAgent(BaseAgent):
    """AI Assistant agent"""
    
    def __init__(self, config: Dict[str, Any], llm: BaseLLM):
        super().__init__(name=config.get("name", "assistant"), llm=llm)

    async def process_message(self, message: str) -> str:
        """Process incoming message"""
        return await self.llm.generate(message) 