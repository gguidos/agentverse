from typing import Dict, Type, Any, Optional, List
from pydantic import BaseModel, Field
import logging
from .base import BaseTool, ToolConfig
from .types import AgentCapability, ToolType, SIMPLE_TOOLS, COMPLEX_TOOLS

logger = logging.getLogger(__name__)

class ToolRegistryConfig(BaseModel):
    """Configuration for tool registry"""
    allow_duplicates: bool = False
    validate_schemas: bool = True
    auto_register_dependencies: bool = True
    skip_existing: bool = True

class ToolRegistry(BaseModel):
    """Registry for agent tools"""
    
    name: str = "ToolRegistry"
    config: ToolRegistryConfig = Field(default_factory=ToolRegistryConfig)
    entries: Dict[str, Type[BaseTool]] = Field(default_factory=dict)
    tool_dependencies: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    model_config = {
        "arbitrary_types_allowed": True
    }
    
    def register(self, capability: AgentCapability, tool_type: str = ToolType.SIMPLE):
        """Register a tool class decorator
        
        Args:
            capability: Tool capability
            tool_type: Tool type (simple or complex)
        """
        def decorator(tool_class: Type[BaseTool]):
            # Register in capability collections
            if tool_type == ToolType.SIMPLE:
                if capability not in SIMPLE_TOOLS:
                    SIMPLE_TOOLS[capability] = []
                SIMPLE_TOOLS[capability].append(tool_class)
            else:
                if capability not in COMPLEX_TOOLS:
                    COMPLEX_TOOLS[capability] = []
                COMPLEX_TOOLS[capability].append(tool_class)
            
            # Also register in entries
            self.entries[tool_class.name] = tool_class
            
            # Add capability to tool class for reference
            if not hasattr(tool_class, 'capabilities'):
                tool_class.capabilities = []
            if capability.value not in tool_class.capabilities:
                tool_class.capabilities.append(capability.value)
            
            logger.debug(f"Registered {tool_type} tool {tool_class.__name__} for capability {capability}")
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
    
    def list_tools(self) -> Dict[str, Any]:
        """List all registered tools with their metadata and organization"""
        try:
            # Organize by both type and capability
            tool_info = {
                "by_type": {
                    "simple": [],
                    "complex": []
                },
                "by_capability": {}
            }

            for name, tool_class in self.entries.items():
                tool_data = {
                    "name": name,
                    "description": getattr(tool_class, "description", "No description available"),
                    "version": getattr(tool_class, "version", "1.0.0"),
                    "permissions": getattr(tool_class, "required_permissions", []),
                    "parameters": getattr(tool_class, "parameters", {}),
                    "capabilities": getattr(tool_class, "capabilities", []),
                    "dependencies": getattr(tool_class, "required_dependencies", {})
                }

                # Organize by type
                if tool_data["dependencies"]:
                    tool_info["by_type"]["complex"].append(tool_data)
                else:
                    tool_info["by_type"]["simple"].append(tool_data)

                # Organize by capability
                for capability in tool_data["capabilities"]:
                    if capability not in tool_info["by_capability"]:
                        tool_info["by_capability"][capability] = {
                            "name": capability,
                            "type": "complex" if tool_data["dependencies"] else "simple",
                            "description": self._get_capability_description(capability),
                            "requires_setup": bool(tool_data["dependencies"]),
                            "setup_requirements": list(tool_data["dependencies"].keys()) if tool_data["dependencies"] else [],
                            "tools": []
                        }
                    tool_info["by_capability"][capability]["tools"].append(tool_data)

            return {
                "tools": tool_info,
                "total_count": len(self.entries),
                "simple_count": len(tool_info["by_type"]["simple"]),
                "complex_count": len(tool_info["by_type"]["complex"])
            }

        except Exception as e:
            logger.error(f"Failed to list tools: {str(e)}")
            raise
    
    def _get_capability_description(self, capability: str) -> str:
        """Get description for a capability"""
        descriptions = {
            "datetime": "Work with dates, times, and time zones",
            "search": "Search and retrieve information from vector stores",
            "memory": "Store and recall information from previous interactions",
            "file_operations": "Handle file system operations",
            "calculate": "Perform mathematical calculations",
            "format": "Format and convert data between different formats"
        }
        return descriptions.get(capability, f"Capability for {capability}")
    
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
    
    def register_with_deps(self, name: str, tool_class: Type[BaseTool], dependencies: Dict[str, Any]):
        """Register a tool with its dependencies"""
        try:
            if name in self.entries:
                if self.config.allow_duplicates:
                    logger.warning(f"Tool '{name}' already registered, overwriting")
                else:
                    logger.debug(f"Tool '{name}' already registered, skipping")
                    return  # Skip instead of raising error
                
            self.entries[name] = tool_class
            self.tool_dependencies[name] = dependencies
            logger.debug(f"Registered tool '{name}' with dependencies")
            
        except Exception as e:
            logger.error(f"Error registering tool '{name}': {str(e)}")
            raise
    
    def get_instance(self, name: str) -> BaseTool:
        """Get a tool instance with its dependencies"""
        if name not in self.entries:
            raise KeyError(f"Tool '{name}' not found")
            
        tool_class = self.entries[name]
        dependencies = self.tool_dependencies.get(name, {})
        return tool_class(**dependencies)

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