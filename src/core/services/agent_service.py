from typing import Dict, Any, List, Optional
from datetime import datetime
from src.core.repositories.agent_repository import AgentRepository
from src.core.agentverse.factories import AgentFactory
from src.core.agentverse.tools import (
    AgentCapability,
    SIMPLE_TOOLS,
    COMPLEX_TOOLS,
    tool_registry,
    ToolRegistry
)
from src.core.agentverse.factories.agent_factory import AgentFactory, AgentConfig
import logging
import uuid

logger = logging.getLogger(__name__)

class AgentService:
    def __init__(
        self, 
        agent_repository: AgentRepository, 
        tool_registry: ToolRegistry = None,
        llm_service: Any = None,
        memory_service: Any = None,
        parser_service: Any = None
    ):
        """Initialize agent service
        
        Args:
            agent_repository: Repository for agent persistence
            tool_registry: Optional tool registry instance
            llm_service: LLM service for agent creation
            memory_service: Memory service for agent creation
            parser_service: Parser service for agent creation
        """
        self.repository = agent_repository
        self.tool_registry = tool_registry
        
        # Initialize agent factory
        self.factory = AgentFactory(
            llm_service=llm_service,
            memory_service=memory_service,
            parser_service=parser_service,
            available_tools={},  # Start with empty tools
            default_memory_class=None
        )
        
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

    async def create_agent(self, config_data: Dict[str, Any], llm_service: Any) -> Dict[str, Any]:
        """Create and persist a new agent"""
        try:
            # Check for duplicates first
            if await self.check_exists(config_data["name"], config_data["type"]):
                raise ValueError(f"Agent with name '{config_data['name']}' and type '{config_data['type']}' already exists")
            
            # Generate agent ID
            agent_id = str(uuid.uuid4())
            
            # Validate capabilities first
            validated_capabilities = self.validate_capabilities(config_data["capabilities"])
            
            # Create agent config
            agent_config = AgentConfig(
                name=config_data["name"],
                capabilities=validated_capabilities,
                metadata={
                    "id": agent_id,  # Add the ID to metadata
                    "type": config_data["type"],
                    "llm_config": config_data.get("llm_config", {}),
                    "form_config": config_data.get("form_config", {})
                }
            )
            
            # Create agent using factory
            agent = await self.factory.get_agent(
                agent_id=agent_id,  # Pass the generated ID
                config=agent_config
            )
            
            # Prepare data for storage
            agent_data = {
                "id": agent_id,  # Use the generated ID
                "name": agent.name,
                "type": config_data["type"],
                "capabilities": [cap.value for cap in validated_capabilities],
                "metadata": agent.metadata,
                "created_at": datetime.utcnow()
            }
            
            # Store in database
            await self.repository.create(agent_data)
            return agent_data
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise ValueError(f"Invalid agent configuration: {str(e)}")
        
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

    async def list_agent_types(self) -> List[Dict[str, Any]]:
        """Get all registered agent types with their metadata
        
        Returns:
            List of agent type information
        """
        from src.core.agentverse.registry import agent_registry
        
        agent_types = []
        for agent_type, agent_class in agent_registry.get_registry().items():
            agent_info = {
                "type": agent_type,
                "name": getattr(agent_class, 'name', agent_type),
                "description": getattr(agent_class, 'description', None),
                "version": getattr(agent_class, 'version', "1.0.0"),
                "capabilities": getattr(agent_class, 'default_capabilities', [])
            }
            agent_types.append(agent_info)
            
        return agent_types 

    async def create_chat_session(self, agent_name: str) -> str:
        try:
            agent = await self.repository.find_by_name(agent_name)
            if not agent:
                raise ValueError(f"Agent {agent_name} not found")
            
            agent_instance = await self.factory.get_agent(
                agent_id=agent["id"],
                config=AgentConfig(**agent)
            )
            
            logger.debug(f"Agent instance created: {agent_instance}")
            await agent_instance.initialize()  # Make sure the agent is ready
            
            session_id = str(uuid.uuid4())
            # Store or log the session if needed
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating chat session: {str(e)}")
            raise

    async def chat(self, agent_name: str, session_id: str, message: str) -> str:
        """Process a chat message"""
        try:
            agent = await self.repository.find_by_name(agent_name)
            if not agent:
                raise ValueError(f"Agent {agent_name} not found")
            
            # Get agent instance
            agent_instance = await self.factory.get_agent(
                agent_id=agent["id"],
                config=AgentConfig(**agent)
            )
            
            # Process message
            response = await agent_instance.process_message(message)
            return response
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            raise 