"""Base agent interface"""

from typing import Dict, Any, List
from src.core.agentverse.entities.agent import AgentConfig
from src.core.agentverse.capabilities import (
    AgentCapability, 
    SIMPLE_TOOLS,
    COMPLEX_TOOLS
)
from src.core.agentverse.tools.base import BaseTool

class BaseAgent:
    """Base agent class"""
    
    def __init__(self, config: AgentConfig):
        """Initialize base agent
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.tools: Dict[str, BaseTool] = {}
        self._initialize_tools()
        
    def _initialize_tools(self):
        """Initialize tools based on agent capabilities"""
        # Combine simple and complex tools
        all_tools = {**SIMPLE_TOOLS, **COMPLEX_TOOLS}
        
        for capability in self.config.capabilities:
            if capability in all_tools:
                for tool_class in all_tools[capability]:
                    tool = tool_class()  # Initialize tool with default config
                    self.tools[tool.name] = tool
                    
    async def get_available_tools(self) -> List[BaseTool]:
        """Get list of tools available to this agent"""
        return list(self.tools.values())
    
    async def process_message(self, message: str) -> str:
        """Process incoming message"""
        raise NotImplementedError() 