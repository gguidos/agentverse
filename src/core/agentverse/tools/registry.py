from typing import Dict, Type, Any, Optional, List
from pydantic import BaseModel, Field
import logging
from src.core.agentverse.tools.base import BaseTool, ToolConfig

logger = logging.getLogger(__name__)

class ToolRegistryConfig(BaseModel):
    """Configuration for tool registry"""
    allow_duplicates: bool = False
    validate_schemas: bool = True
    auto_register_dependencies: bool = True

class ToolRegistry(BaseModel):
    """Registry for agent tools"""
    
    name: str = "ToolRegistry"
    config: ToolRegistryConfig = Field(default_factory=ToolRegistryConfig)
    entries: Dict[str, Type[BaseTool]] = Field(default_factory=dict)
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
    def register(self, *names: str, config: Optional[ToolConfig] = None):
        """Register a tool class with multiple names
        
        Args:
            *names: Tool names to register
            config: Optional tool configuration
        """
        def decorator(tool_class: Type[BaseTool]):
            # Validate tool class
            if not issubclass(tool_class, BaseTool):
                raise ValueError(f"Class {tool_class.__name__} must inherit from BaseTool")
            
            # Register with all provided names
            registry_names = list(names)
            if not registry_names:
                registry_names = [tool_class.name]
            
            for name in registry_names:
                if name in self.entries and not self.config.allow_duplicates:
                    raise KeyError(f"Tool '{name}' already registered")
                    
                # Validate tool schema if enabled
                if self.config.validate_schemas:
                    try:
                        tool_instance = tool_class(config=config)
                        tool_instance.get_schema()
                    except Exception as e:
                        logger.error(f"Tool schema validation failed for {name}: {str(e)}")
                        raise ValueError(f"Invalid tool schema for {name}: {str(e)}")
                
                self.entries[name] = tool_class
                logger.info(f"Registered tool '{name}' ({tool_class.__name__})")
            
            return tool_class
        return decorator
    
    def get(self, name: str, config: Optional[ToolConfig] = None, **kwargs) -> BaseTool:
        """Get a tool instance
        
        Args:
            name: Tool name
            config: Optional tool configuration
            **kwargs: Additional arguments for tool initialization
        """
        if name not in self.entries:
            raise KeyError(f"Tool '{name}' not found in registry")
            
        try:
            tool_class = self.entries[name]
            if config:
                return tool_class(config=config, **kwargs)
            return tool_class(**kwargs)
            
        except Exception as e:
            logger.error(f"Failed to instantiate tool '{name}': {str(e)}")
            raise
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all registered tools with their schemas"""
        try:
            return {
                name: {
                    "schema": tool().get_schema(),
                    "version": getattr(tool, "version", "1.0.0"),
                    "permissions": getattr(tool, "required_permissions", [])
                }
                for name, tool in self.entries.items()
            }
        except Exception as e:
            logger.error(f"Failed to list tools: {str(e)}")
            raise
    
    def get_tool_names(self) -> List[str]:
        """Get list of registered tool names"""
        return list(self.entries.keys())
    
    def has_tool(self, name: str) -> bool:
        """Check if tool is registered"""
        return name in self.entries
    
    def unregister(self, name: str) -> None:
        """Unregister a tool"""
        if name in self.entries:
            del self.entries[name]
            logger.info(f"Unregistered tool '{name}'")
    
    def clear(self) -> None:
        """Clear all registered tools"""
        self.entries.clear()
        logger.info("Cleared tool registry")

# Create singleton instance
tool_registry = ToolRegistry()

# Example usage:
"""
@tool_registry.register("memory", "memory_search")
class MemoryTool(BaseTool):
    name = "memory"
    # ...

# Get tool instance
memory_tool = tool_registry.get(
    "memory",
    config=MemoryToolConfig(max_results=20),
    memory_store=memory_store,
    llm=llm_service
)

# List available tools
available_tools = tool_registry.list_tools()
""" 