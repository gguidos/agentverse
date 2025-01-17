from typing import Dict, Any, Optional, List
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from src.core.infrastructure.db.mongo_client import MongoDBClient

class AgentRepository:
    """Repository for agent persistence"""
    
    def __init__(self, mongo_client: MongoDBClient):
        self.collection = mongo_client.db.agents
        
    def _serialize_agent(self, agent: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB document to serializable dict"""
        if agent and "_id" in agent:
            agent["_id"] = str(agent["_id"])
        return agent
        
    async def create(self, agent_data: Dict[str, Any]) -> str:
        """Create new agent"""
        try:
            result = await self.collection.insert_one(agent_data)
            return agent_data["id"]  # Return the string ID we generated
        except DuplicateKeyError:
            raise ValueError(f"Agent with name '{agent_data['name']}' and type '{agent_data['type']}' already exists")
        
    async def get(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        result = await self.collection.find_one({"id": agent_id})  # Use string id
        return self._serialize_agent(result) if result else None
        
    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents"""
        cursor = self.collection.find({})
        agents = await cursor.to_list(length=None)
        return [self._serialize_agent(agent) for agent in agents]
        
    async def find_by_name_and_type(self, name: str, type: str) -> Optional[Dict[str, Any]]:
        """Find agent by name and type"""
        result = await self.collection.find_one({"name": name, "type": type})
        return self._serialize_agent(result) if result else None
        
    async def update(self, agent_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update agent by ID"""
        try:
            result = await self.collection.find_one_and_update(
                {"id": agent_id},  # Use string id
                {"$set": update_data},
                return_document=True
            )
            return self._serialize_agent(result) if result else None
        except Exception as e:
            raise ValueError(f"Failed to update agent: {str(e)}") 
        
    async def update_by_name_type(
        self, 
        name: str, 
        type: str, 
        update_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update agent by name and type"""
        try:
            result = await self.collection.find_one_and_update(
                {"name": name, "type": type},
                {"$set": update_data},
                return_document=True
            )
            return self._serialize_agent(result) if result else None
        except Exception as e:
            raise ValueError(f"Failed to update agent: {str(e)}") 