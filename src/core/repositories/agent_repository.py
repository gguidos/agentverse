from typing import Optional, List
from datetime import datetime
from src.core.infrastructure.db.mongo_client import MongoDBClient
import logging

logger = logging.getLogger(__name__)

class AgentRepository:
    def __init__(self, mongo_client: MongoDBClient):
        self.mongo_client = mongo_client
        self.collection_name = "agents"

    async def create_agent(self, agent_data: dict) -> dict:
        """Create a new agent"""
        try:
            agent_data["created_at"] = datetime.utcnow()
            agent_data["updated_at"] = datetime.utcnow()
            
            agent_data["_id"] = await self.mongo_client.insert_one(
                self.collection_name,
                agent_data
            )
            
            logger.info(f"Created agent: {agent_data['name']}")
            return agent_data
            
        except Exception as e:
            logger.error(f"Failed to create agent: {str(e)}")
            raise

    async def get_agent(self, agent_name: str) -> Optional[dict]:
        """Get agent by name"""
        try:
            return await self.mongo_client.find_one(
                self.collection_name,
                {"name": agent_name}
            )
        except Exception as e:
            logger.error(f"Failed to get agent: {str(e)}")
            raise

    async def list_agents(self) -> List[dict]:
        """List all agents"""
        try:
            return await self.mongo_client.find_many(
                self.collection_name,
                query={},
                sort=[("created_at", -1)]
            )
        except Exception as e:
            logger.error(f"Failed to list agents: {str(e)}")
            raise

    async def update_agent(self, agent_name: str, update_data: dict) -> Optional[dict]:
        """Update agent data"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            success = await self.mongo_client.update_one(
                self.collection_name,
                {"name": agent_name},
                {"$set": update_data}
            )
            if success:
                return await self.get_agent(agent_name)
            return None
        except Exception as e:
            logger.error(f"Failed to update agent: {str(e)}")
            raise

    async def delete_agent(self, agent_name: str) -> bool:
        """Delete an agent"""
        try:
            return await self.mongo_client.delete_one(
                self.collection_name,
                {"name": agent_name}
            )
        except Exception as e:
            logger.error(f"Failed to delete agent: {str(e)}")
            raise 