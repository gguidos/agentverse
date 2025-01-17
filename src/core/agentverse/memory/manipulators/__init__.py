"""Memory manipulators module"""

from typing import Dict, Type

from src.core.agentverse.memory.manipulators.base import BaseMemoryManipulator
from src.core.agentverse.memory.manipulators.simple import SimpleMemoryManipulator
from src.core.agentverse.memory.manipulators.summarize import SummarizeMemoryManipulator
from src.core.agentverse.memory.manipulators.filter import FilterMemoryManipulator

# Registry of manipulator implementations
manipulator_registry: Dict[str, Type[BaseMemoryManipulator]] = {
    "simple": SimpleMemoryManipulator,
    "summarize": SummarizeMemoryManipulator,
    "filter": FilterMemoryManipulator,
    "default": SimpleMemoryManipulator
}

__all__ = [
    "BaseMemoryManipulator",
    "SimpleMemoryManipulator",
    "SummarizeMemoryManipulator", 
    "FilterMemoryManipulator",
    "manipulator_registry"
]

# Version
__version__ = "1.1.0" 