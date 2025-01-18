from typing import Any
import logging
from .registry import tool_registry
from .types import AgentCapability, SIMPLE_TOOLS, COMPLEX_TOOLS, ToolType
from .datetime_tool import DateTimeTool
from .search_tool import SearchTool
from .memory_tool import MemoryTool
from .file_tool import FileTool
from .utility_tool import CalculateTool, FormatTool
from .knowledge_tool import KnowledgeTool
from .url_tool import URLTool
from .form_tool import FormTool

logger = logging.getLogger(__name__)

def register_default_tools(
    vectorstore=None,
    llm=None,
    memory_store=None,
    redis_client=None
) -> Any:
    """Register default tools in the tool registry"""
    logger.debug("Registering default tools")
    
    # Register complex tools with dependencies
    if vectorstore and llm:
        # Register search tool
        tool_registry.register_with_deps("search", SearchTool, {"vectorstore": vectorstore})
        
        # Register knowledge tool
        logger.debug(f"Registering knowledge tool with type {ToolType.COMPLEX}")
        COMPLEX_TOOLS[AgentCapability.KNOWLEDGE] = [KnowledgeTool]
        tool_registry.register_with_deps("knowledge", KnowledgeTool, {
            "vectorstore": vectorstore,
            "llm": llm,
            "redis_client": redis_client
        })
        
        # Register URL tool
        SIMPLE_TOOLS[AgentCapability.URL] = [URLTool]
        tool_registry.register_with_deps("url", URLTool, {})
        
        # Register form tool
        tool_registry.register_with_deps("form", FormTool, {
            "vectorstore": vectorstore,
            "llm": llm
        })
    
    if memory_store and llm:
        tool_registry.register_with_deps("memory", MemoryTool, {
            "memory_store": memory_store,
            "llm": llm
        })
    
    return tool_registry 