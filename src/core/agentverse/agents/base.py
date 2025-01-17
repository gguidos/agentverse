"""Base agent interface"""

from typing import Dict, Any
from src.core.agentverse.entities.agent import AgentConfig

class BaseAgent:
    """Base agent class"""
    
    def __init__(self, config: AgentConfig):
        """Initialize base agent
        
        Args:
            config: Agent configuration
        """
        self.config = config
        
    async def process_message(self, message: str) -> str:
        """Process incoming message"""
        raise NotImplementedError() 