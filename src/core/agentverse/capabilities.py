from enum import Enum
from typing import Dict, Type, List, Any
import logging
from src.core.agentverse.tools.base import BaseTool
from src.core.agentverse.tools.search_tool import SearchTool
from src.core.agentverse.tools.memory_tool import MemoryTool
from src.core.agentverse.tools.datetime_tool import DateTimeTool
from src.core.agentverse.tools.file_tool import FileTool
from src.core.agentverse.tools.utility_tool import CalculateTool, FormatTool

logger = logging.getLogger(__name__)

class AgentCapability(str, Enum):
    """Available agent capabilities"""
    DATETIME = "datetime"      # Simple tool, no dependencies
    CALCULATE = "calculate"    # Simple tool, no dependencies
    FORMAT = "format"         # Simple tool, no dependencies
    SEARCH = "search"         # Complex tool, needs vectorstore
    MEMORY = "memory"         # Complex tool, needs memory store
    FILE_OPERATIONS = "file_operations"  # Complex tool, needs file system

# Separate tools into simple (no dependencies) and complex (with dependencies)
SIMPLE_TOOLS = {
    AgentCapability.DATETIME: [DateTimeTool],
    AgentCapability.CALCULATE: [CalculateTool],
    AgentCapability.FORMAT: [FormatTool]
}

COMPLEX_TOOLS = {
    AgentCapability.SEARCH: [SearchTool],
    AgentCapability.MEMORY: [MemoryTool],
    AgentCapability.FILE_OPERATIONS: [FileTool]
}

def register_default_tools(
    vectorstore=None,
    llm=None,
    memory_store=None,
    redis_client=None
) -> Any:
    """Register default tools in the tool registry"""
    from src.core.agentverse.tools.registry import tool_registry
    logger.debug("Registering default tools")
    
    registered_tools = set()
    
    # Register simple tools (no dependencies)
    for cap, tools in SIMPLE_TOOLS.items():
        for tool in tools:
            if tool.name not in registered_tools:
                try:
                    tool_registry.register_with_deps(tool.name, tool, {})
                    registered_tools.add(tool.name)
                    logger.debug(f"Registered simple tool: {tool.name}")
                except Exception as e:
                    logger.warning(f"Failed to register tool {tool.name}: {str(e)}")
    
    # Register complex tools only if dependencies are available
    if vectorstore and llm:
        for tool in COMPLEX_TOOLS.get(AgentCapability.SEARCH, []):
            if tool.name not in registered_tools:
                try:
                    tool_registry.register_with_deps(tool.name, tool, {"vectorstore": vectorstore})
                    registered_tools.add(tool.name)
                    logger.debug(f"Registered search tool: {tool.name}")
                except Exception as e:
                    logger.warning(f"Failed to register tool {tool.name}: {str(e)}")
            
    if memory_store and llm:
        for tool in COMPLEX_TOOLS.get(AgentCapability.MEMORY, []):
            if tool.name not in registered_tools:
                try:
                    tool_registry.register_with_deps(tool.name, tool, {
                        "memory_store": memory_store,
                        "llm": llm
                    })
                    registered_tools.add(tool.name)
                    logger.debug(f"Registered memory tool: {tool.name}")
                except Exception as e:
                    logger.warning(f"Failed to register tool {tool.name}: {str(e)}")
    
    return tool_registry 