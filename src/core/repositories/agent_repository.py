from typing import Dict, Any, Optional
from bson import ObjectId
from src.core.infrastructure.db.mongo_client import MongoDBClient

class AgentRepository:
    """Repository for agent persistence"""
    
    def __init__(self, mongo_client: MongoDBClient):
        self.collection = mongo_client.db.agents
        
    async def create(self, agent_data: Dict[str, Any]) -> str:
        """Create new agent"""
        result = await self.collection.insert_one(agent_data)
        return str(result.inserted_id)
        
    async def get(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        result = await self.collection.find_one({"_id": ObjectId(agent_id)})
        return result if result else None 