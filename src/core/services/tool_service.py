from typing import Dict, Any, List
import logging
from src.core.agentverse.tools import (
    ToolRegistry,
    SIMPLE_TOOLS,
    COMPLEX_TOOLS,
    AgentCapability
)

logger = logging.getLogger(__name__)

class ToolService:
    def __init__(self, tool_registry: ToolRegistry):
        self.registry = tool_registry

    async def list_tools(self) -> Dict[str, Any]:
        """Get all available tools with their metadata"""
        try:
            tool_info = {}
            for name, tool_class in self.registry.entries.items():
                try:
                    metadata = tool_class.get_metadata()
                    tool_info[name] = {
                        **metadata,
                        "type": "simple" if name in [t.name for tools in SIMPLE_TOOLS.values() for t in tools] else "complex"
                    }
                except Exception as e:
                    logger.warning(f"Error getting info for tool {name}: {str(e)}")
                    continue
            
            return {
                "tools": tool_info,
                "count": len(tool_info)
            }
            
        except Exception as e:
            logger.error(f"Failed to list tools: {str(e)}")
            raise

    async def get_tool(self, name: str) -> Dict[str, Any]:
        """Get specific tool information"""
        if not self.registry.has_tool(name):
            raise ValueError(f"Tool '{name}' not found")
            
        tool_class = self.registry.entries[name]
        metadata = tool_class.get_metadata()
        return {
            **metadata,
            "type": "simple" if name in [t.name for tools in SIMPLE_TOOLS.values() for t in tools] else "complex"
        }

    async def get_tool_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """Get tools for a specific capability"""
        tools = []
        if capability in SIMPLE_TOOLS:
            tools.extend(SIMPLE_TOOLS[capability])
        if capability in COMPLEX_TOOLS:
            tools.extend(COMPLEX_TOOLS[capability])
            
        return [await self.get_tool(tool.name) for tool in tools] 

    async def list_capabilities(self) -> List[Dict[str, Any]]:
        """Get all available capabilities and their tools"""
        capabilities = []
        
        # Add simple tools
        for cap, tools in SIMPLE_TOOLS.items():
            capabilities.append({
                "name": cap.value,
                "type": "simple",
                "description": self._get_capability_description(cap),
                "requires_setup": False,
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "version": tool.version,
                        "parameters": tool.parameters
                    }
                    for tool in tools
                ]
            })
            
        # Add complex tools
        for cap, tools in COMPLEX_TOOLS.items():
            capabilities.append({
                "name": cap.value,
                "type": "complex",
                "description": self._get_capability_description(cap),
                "requires_setup": True,
                "setup_requirements": self._get_setup_requirements(cap),
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "version": tool.version,
                        "parameters": tool.parameters
                    }
                    for tool in tools
                ]
            })
            
        return capabilities

    def _get_capability_description(self, capability: AgentCapability) -> str:
        """Get human-readable description for a capability"""
        descriptions = {
            AgentCapability.DATETIME: "Work with dates, times, and time zones",
            AgentCapability.CALCULATE: "Perform mathematical calculations",
            AgentCapability.FORMAT: "Format and transform text and data",
            AgentCapability.SEARCH: "Search and retrieve information from vector stores",
            AgentCapability.MEMORY: "Store and recall information from previous interactions",
            AgentCapability.FILE_OPERATIONS: "Read, write, and manage files"
        }
        return descriptions.get(capability, "No description available")

    def _get_setup_requirements(self, capability: AgentCapability) -> List[str]:
        """Get setup requirements for complex capabilities"""
        requirements = {
            AgentCapability.SEARCH: ["Vector store configuration", "Embeddings model"],
            AgentCapability.MEMORY: ["Memory store configuration", "LLM configuration"],
            AgentCapability.FILE_OPERATIONS: ["File system permissions", "Storage configuration"]
        }
        return requirements.get(capability, [])

    async def get_capability(self, capability_name: str) -> Dict[str, Any]:
        """Get specific capability information and its tools"""
        try:
            # Convert string to enum
            try:
                cap = AgentCapability(capability_name)
            except ValueError:
                raise ValueError(f"Invalid capability: {capability_name}")

            # Get tools for this capability
            tools = []
            if cap in SIMPLE_TOOLS:
                tools = SIMPLE_TOOLS[cap]
                cap_type = "simple"
            elif cap in COMPLEX_TOOLS:
                tools = COMPLEX_TOOLS[cap]
                cap_type = "complex"
            else:
                raise ValueError(f"Capability '{capability_name}' not found")

            return {
                "name": cap.value,
                "type": cap_type,
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "version": tool.version
                    }
                    for tool in tools
                ]
            }

        except Exception as e:
            logger.error(f"Error getting capability {capability_name}: {str(e)}")
            raise 