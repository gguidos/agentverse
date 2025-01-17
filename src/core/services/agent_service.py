from typing import Dict, Any, List, Optional
from datetime import datetime
from src.core.repositories.agent_repository import AgentRepository
from src.core.agentverse.factories import AgentFactory
from src.core.agentverse.factories.agent import AgentFactoryConfig
from src.core.agentverse.tools import (
    AgentCapability,
    SIMPLE_TOOLS,
    COMPLEX_TOOLS,
    tool_registry,
    ToolRegistry
)
import logging

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self, agent_repository: AgentRepository, tool_registry: ToolRegistry = None):
        """Initialize agent service
        
        Args:
            agent_repository: Repository for agent persistence
            tool_registry: Optional tool registry instance
        """
        self.repository = agent_repository
        self.tool_registry = tool_registry or tool_registry  # Use provided or singleton
        
    async def check_exists(self, name: str, type: str) -> bool:
        """Check if agent with same name and type exists"""
        agent = await self.repository.find_by_name_and_type(name, type)
        return agent is not None
        
    def validate_capabilities(self, capabilities: List[str]) -> List[AgentCapability]:
        """Validate and convert capability strings to enum"""
        valid_capabilities = []
        # Combine all available capabilities
        all_tools = {**SIMPLE_TOOLS, **COMPLEX_TOOLS}
        
        for cap in capabilities:
            try:
                capability = AgentCapability(cap)
                if capability not in all_tools:
                    raise ValueError(f"Capability '{cap}' is not supported")
                valid_capabilities.append(capability)
            except ValueError as e:
                raise ValueError(f"Invalid capability: {cap}")
        return valid_capabilities

    async def create_agent(self, config: AgentFactoryConfig, llm_service: Any) -> Dict[str, Any]:
        """Create and persist a new agent"""
        # Check for duplicates first
        if await self.check_exists(config.name, config.type):
            raise ValueError(f"Agent with name '{config.name}' and type '{config.type}' already exists")
            
        # Validate capabilities first
        config.capabilities = self.validate_capabilities(config.capabilities)
        
        # Create agent using factory
        agent = await AgentFactory.create(
            config=config,
            llm_service=llm_service
        )
        
        # Prepare data for storage
        agent_data = {
            "id": agent.config.id,
            "name": agent.config.name,
            "type": agent.config.type,
            "capabilities": agent.config.capabilities,
            "metadata": agent.config.metadata,
            "created_at": datetime.utcnow()
        }
        
        # Store in database
        await self.repository.create(agent_data)
        return agent
        
    async def list_agents(self) -> Dict[str, Any]:
        """Get all agents"""
        try:
            logger.debug("Fetching agents from repository")
            agents = await self.repository.list_agents()
            
            logger.debug(f"Processing {len(agents) if agents else 0} agents")
            
            if not agents:
                logger.debug("No agents found")
                return {
                    "agents": [],
                    "count": 0
                }
            
            formatted_agents = []
            for agent in agents:
                try:
                    formatted_agent = {
                        "id": agent.get("id"),
                        "name": agent.get("name"),
                        "type": agent.get("type"),
                        "capabilities": agent.get("capabilities", []),
                        "metadata": agent.get("metadata", {}),
                        "created_at": agent.get("created_at"),
                        "updated_at": agent.get("updated_at")
                    }
                    if all(formatted_agent.get(key) for key in ["id", "name", "type"]):
                        formatted_agents.append(formatted_agent)
                except Exception as e:
                    logger.warning(f"Error formatting agent: {str(e)}")
                    continue
            
            logger.debug(f"Returning {len(formatted_agents)} formatted agents")
            return {
                "agents": formatted_agents,
                "count": len(formatted_agents)
            }
            
        except Exception as e:
            logger.error(f"Error in list_agents service: {str(e)}", exc_info=True)
            raise
        
    async def update_agent(self, agent_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update agent capabilities"""
        # Get existing agent
        agent = await self.repository.get(agent_id)
        if not agent:
            raise ValueError(f"Agent with id '{agent_id}' not found")
        
        # Update agent data
        updated = await self.repository.update(
            agent_id,
            {
                **update_data,
                "updated_at": datetime.utcnow()
            }
        )
        return updated 
        
    async def update_agent_by_name_type(
        self, 
        name: str, 
        type: str, 
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update agent by name and type"""
        # Get existing agent
        agent = await self.repository.find_by_name_and_type(name, type)
        if not agent:
            raise ValueError(f"Agent with name '{name}' and type '{type}' not found")
        
        # Update agent data
        updated = await self.repository.update_by_name_type(
            name,
            type,
            {
                **update_data,
                "updated_at": datetime.utcnow()
            }
        )
        return updated 

    async def list_capabilities(self) -> List[Dict[str, Any]]:
        """Get all available capabilities and their tools"""
        capabilities = []
        
        # Add simple tools
        for cap, tools in SIMPLE_TOOLS.items():
            capabilities.append({
                "name": cap.value,
                "type": "simple",
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "version": tool.version
                    }
                    for tool in tools
                ]
            })
            
        # Add complex tools
        for cap, tools in COMPLEX_TOOLS.items():
            capabilities.append({
                "name": cap.value,
                "type": "complex",
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "version": tool.version
                    }
                    for tool in tools
                ]
            })
            
        return capabilities

    async def list_tools(self) -> Dict[str, Any]:
        """Get all available tools and their schemas"""
        return tool_registry.list_tools() 