"""Agent Package"""

from typing import Dict, Type
from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.agents.assistant import AssistantAgent
from src.core.agentverse.agents.user import UserAgent

# Register agent types
AGENT_TYPES: Dict[str, Type[BaseAgent]] = {
    "assistant": AssistantAgent,
    "user": UserAgent
}

__all__ = [
    "BaseAgent",
    "AssistantAgent",
    "UserAgent",
    "AGENT_TYPES"
] 