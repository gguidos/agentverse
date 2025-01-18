from enum import Enum, auto
from typing import Dict, Type, List
from .base import BaseTool

class AgentCapability(str, Enum):
    """Available agent capabilities"""
    DATETIME = "datetime"      # Simple tool, no dependencies
    CALCULATE = "calculate"    # Simple tool, no dependencies
    FORMAT = "format"         # Simple tool, no dependencies
    SEARCH = "search"         # Complex tool, needs vectorstore
    MEMORY = "memory"         # Complex tool, needs memory store
    FILE_OPERATIONS = "file_operations"  # Complex tool, needs file system
    KNOWLEDGE = "knowledge"
    FILE = "file"
    URL = "url"
    FORM = "form"
    
class ToolType(str, Enum):
    """Tool types based on dependency requirements"""
    SIMPLE = "simple"
    COMPLEX = "complex"

# Tool mappings will be populated after tool classes are defined
SIMPLE_TOOLS: Dict[AgentCapability, List[Type[BaseTool]]] = {}
COMPLEX_TOOLS: Dict[AgentCapability, List[Type[BaseTool]]] = {} 