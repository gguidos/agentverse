"""Environment Package"""

from typing import Dict, Type
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.environment.chat import ChatEnvironment
from src.core.agentverse.environment.evaluation import EvaluationEnvironment
from src.core.agentverse.environment.models import EnvironmentStepResult

# Register environment types
ENVIRONMENT_TYPES: Dict[str, Type[BaseEnvironment]] = {
    "chat": ChatEnvironment,
    "evaluation": EvaluationEnvironment,
    "default": ChatEnvironment
}

__all__ = [
    "BaseEnvironment",
    "ChatEnvironment",
    "EvaluationEnvironment",
    "ENVIRONMENT_TYPES",
    "EnvironmentStepResult"
] 