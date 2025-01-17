"""
Agent registry module
"""

from typing import Dict, Type
from src.core.agentverse.agents import BaseAgent
from src.core.agentverse.agents.assistant import AssistantAgent
from src.core.agentverse.agents.user import UserAgent
from src.core.agentverse.testing.mocks.agent import MockAgent

# Registry of agent implementations
agent_registry: Dict[str, Type[BaseAgent]] = {
    "mock": MockAgent,
    "assistant": AssistantAgent,
    "user": UserAgent,
    "default": AssistantAgent
} 