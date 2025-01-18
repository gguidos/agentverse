from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from pydantic import BaseModel
import logging
from src.core.dependencies.di_container import get_llm_service, get_agent_service
from src.core.services.vectorstore_service import VectorstoreService
from src.core.dependencies.vectorstore_orchestrator_dependency import get_vectorstore_orchestrator
from src.core.services.agent_service import AgentService
from fastapi.encoders import jsonable_encoder
from bson import ObjectId

router = APIRouter()
logger = logging.getLogger(__name__)

class CreateAgentRequest(BaseModel):
    """Request model for agent creation"""
    name: str
    type: str = "assistant"
    capabilities: list = []
    llm_config: Dict[str, Any] = {"type": "mock"}
    metadata: Dict[str, Any] = {}

class UpdateAgentRequest(BaseModel):
    """Request model for agent update"""
    capabilities: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/agents")
async def create_agent(
    config: Dict[str, Any],
    agent_service: AgentService = Depends(get_agent_service),
    llm_service: Any = Depends(get_llm_service)
) -> Dict[str, Any]:
    """Create a new agent"""
    try:
        # Create agent
        agent = await agent_service.create_agent(config, llm_service)
        
        # Convert response to JSON-serializable format
        serialized_agent = jsonable_encoder(agent, custom_encoder={ObjectId: str})
        
        return {
            "status": "success",
            "data": serialized_agent,
            "message": "Agent created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent configuration: {str(e)}"
        )

@router.get("/agent/types")
async def list_agent_types(
    agent_service: AgentService = Depends(get_agent_service)
):
    """List all agent types"""
    try:
        agent_types = await agent_service.list_agent_types()
        return {
            "agent_types": agent_types,
            "count": len(agent_types)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list agent types: {str(e)}"
        )

@router.get("/agents")
@router.get("/agents/")
async def list_agents(
    agent_service: AgentService = Depends(get_agent_service)
):
    """List all agents"""
    try:
        logger.debug("Requesting agents list from service")
        result = await agent_service.list_agents()
        
        return {
            "status": "success",
            "data": result,
            "message": "Agents retrieved successfully",
            "error": None
        }
    except Exception as e:
        logger.error(f"Error listing agents: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.patch("/agents")
async def update_agent(
    request: UpdateAgentRequest,
    name: str,
    type: str = "assistant",
    agent_service: AgentService = Depends(get_agent_service)
):
    """Update an agent by name and type"""
    try:
        agent = await agent_service.update_agent_by_name_type(
            name, 
            type, 
            request.model_dump(exclude_unset=True)
        )
        return {
            "status": "success",
            "data": agent
        }
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating agent: {str(e)}"
        )

@router.post("/agents/{agent_name}/chat/session")
async def create_chat_session(
    agent_name: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> Dict[str, Any]:
    """Create a new chat session for an agent"""
    try:
        session_id = await agent_service.create_chat_session(agent_name)
        logger.debug(f"Created chat session: {session_id}")  # Debug log
        return {
            "status": "success",
            "session_id": session_id
        }
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/agents/{agent_name}/chat/{session_id}")
async def chat_with_agent(
    agent_name: str,
    session_id: str,
    message: Dict[str, str],
    agent_service: AgentService = Depends(get_agent_service)
) -> Dict[str, Any]:
    """Send a message to an agent"""
    try:
        response = await agent_service.chat(
            agent_name,
            session_id,
            message["message"]
        )

        logger.info(response)
        return {
            "status": "success",
            "data": {
                "response": response
            },
            "message": "Message processed"
        }
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )