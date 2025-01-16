"""
Memory Manipulators Module

This module provides data manipulation for memory operations:

1. Vector Manipulator:
   - Embedding generation
   - Vector normalization
   - Dimension reduction

2. Document Manipulator:
   - Text processing
   - Metadata extraction
   - Format conversion
"""

from typing import Dict, Type

from src.core.agentverse.memory.manipulators.base import BaseManipulator
from src.core.agentverse.memory.manipulators.vector import VectorManipulator
from src.core.agentverse.memory.manipulators.document import DocumentManipulator

# Manipulator registry
MANIPULATORS: Dict[str, Type[BaseManipulator]] = {
    "vector": VectorManipulator,
    "document": DocumentManipulator
}

def get_manipulator(name: str) -> Type[BaseManipulator]:
    """Get manipulator by name
    
    Args:
        name: Manipulator name
        
    Returns:
        Manipulator class
        
    Raises:
        ValueError: If manipulator not found
    """
    if name not in MANIPULATORS:
        raise ValueError(f"Manipulator not found: {name}")
    return MANIPULATORS[name]

__all__ = [
    'BaseManipulator',
    'VectorManipulator',
    'DocumentManipulator',
    'get_manipulator'
]

# Version
__version__ = "1.1.0" 