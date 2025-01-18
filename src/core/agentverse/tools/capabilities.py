from typing import Any
import logging
from .types import AgentCapability, SIMPLE_TOOLS, COMPLEX_TOOLS
from .datetime_tool import DateTimeTool
from .search_tool import SearchTool
from .memory_tool import MemoryTool
from .file_tool import FileTool
from .utility_tool import CalculateTool, FormatTool

logger = logging.getLogger(__name__)

def register_default_tools(
    vectorstore=None,
    llm=None,
    memory_store=None,
    redis_client=None
) -> Any:
    """Register default tools in the tool registry"""
    logger.debug("Registering default tools")
    
    # Tools are already registered via decorators
    # Just need to handle dependencies for complex tools
    
    if vectorstore and llm:
        tool_registry.register_with_deps("search", SearchTool, {"vectorstore": vectorstore})
            
    if memory_store and llm:
        tool_registry.register_with_deps("memory", MemoryTool, {
            "memory_store": memory_store,
            "llm": llm
        })
    
    return tool_registry 