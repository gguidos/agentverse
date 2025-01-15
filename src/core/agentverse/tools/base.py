from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel

class ToolResult(BaseModel):
    """Base model for tool execution results"""
    success: bool
    result: Any
    error: str = None

class AgentTool(ABC):
    """Base class for agent tools"""
    name: str
    description: str
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        pass

    def to_dict(self) -> Dict[str, str]:
        """Convert tool to dictionary format"""
        return {
            "name": self.name,
            "description": self.description
        } 