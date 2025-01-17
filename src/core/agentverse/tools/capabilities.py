from typing import Any
import logging
from .types import AgentCapability, SIMPLE_TOOLS, COMPLEX_TOOLS
from .datetime_tool import DateTimeTool
from .search_tool import SearchTool
from .memory_tool import MemoryTool
from .file_tool import FileTool
from .utility_tool import CalculateTool, FormatTool

logger = logging.getLogger(__name__)

def initialize_tool_mappings():
    """Initialize tool mappings"""
    # Simple tools
    SIMPLE_TOOLS[AgentCapability.DATETIME] = [DateTimeTool]
    SIMPLE_TOOLS[AgentCapability.CALCULATE] = [CalculateTool]
    SIMPLE_TOOLS[AgentCapability.FORMAT] = [FormatTool]
    
    # Complex tools
    COMPLEX_TOOLS[AgentCapability.SEARCH] = [SearchTool]
    COMPLEX_TOOLS[AgentCapability.MEMORY] = [MemoryTool]
    COMPLEX_TOOLS[AgentCapability.FILE_OPERATIONS] = [FileTool]

def register_default_tools(
    vectorstore=None,
    llm=None,
    memory_store=None,
    redis_client=None
) -> Any:
    """Register default tools in the tool registry"""
    from .registry import tool_registry
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