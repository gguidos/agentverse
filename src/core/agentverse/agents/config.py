"""
Agent configuration module
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    """Agent configuration"""
    name: str
    description: Optional[str] = None
    llm_config: Dict[str, Any] = Field(default_factory=dict)
    memory_config: Optional[Dict[str, Any]] = None
    tools_config: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AssistantAgentConfig(AgentConfig):
    """Assistant agent configuration"""
    system_prompt: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    stop_sequences: List[str] = Field(default_factory=list)

class UserAgentConfig(AgentConfig):
    """User agent configuration"""
    user_id: str
    preferences: Dict[str, Any] = Field(default_factory=dict)

class FunctionAgentConfig(AgentConfig):
    """Function agent configuration"""
    functions: List[Dict[str, Any]] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)

__all__ = [
    "AgentConfig",
    "AssistantAgentConfig",
    "UserAgentConfig",
    "FunctionAgentConfig"
] 