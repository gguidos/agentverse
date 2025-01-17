"""Environment implementations"""

from typing import Dict, Type
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.chat import ChatEnvironment
from src.core.agentverse.environment.models import EnvironmentStepResult

# Register environment types
ENVIRONMENT_TYPES: Dict[str, Type[BaseEnvironment]] = {
    "chat": ChatEnvironment,
    "default": ChatEnvironment  # Default to chat environment
}

__all__ = [
    "BaseEnvironment",
    "ChatEnvironment",
    "ENVIRONMENT_TYPES",
    "EnvironmentStepResult"
] 