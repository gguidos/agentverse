from src.core.agentverse.memory.manipulators.base import BaseMemoryManipulator
from src.core.agentverse.memory.manipulators.registry import manipulator_registry

@manipulator_registry.register("basic")
class BasicMemoryManipulator(BaseMemoryManipulator):
    """Basic memory manipulator with no special behavior"""
    
    async def manipulate_memory(self) -> None:
        """Pass-through manipulator"""
        return None
        
    async def reset(self) -> None:
        """Reset manipulator state"""
        self.buffer = ""
        self.last_processed_id = 0 