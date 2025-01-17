from typing import Dict, Any, List, Optional
from datetime import datetime
from src.core.repositories.agent_repository import AgentRepository
from src.core.agentverse.factories import AgentFactory
from src.core.agentverse.factories.agent import AgentFactoryConfig

class AgentService:
    def __init__(self, agent_repository: AgentRepository):
        self.repository = agent_repository
        
    async def check_exists(self, name: str, type: str) -> bool:
        """Check if agent with same name and type exists"""
        agent = await self.repository.find_by_name_and_type(name, type)
        return agent is not None
        
    async def create_agent(self, config: AgentFactoryConfig, llm_service: Any) -> Dict[str, Any]:
        """Create and persist a new agent"""
        # Check for duplicates first
        if await self.check_exists(config.name, config.type):
            raise ValueError(f"Agent with name '{config.name}' and type '{config.type}' already exists")
            
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
        
    async def list_agents(self) -> List[Dict[str, Any]]:
        """Get all agents"""
        return await self.repository.list_agents() 
        
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