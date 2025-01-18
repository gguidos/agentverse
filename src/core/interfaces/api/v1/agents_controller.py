from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from pydantic import BaseModel
from json import JSONEncoder
import logging
import uuid
from src.core.agentverse.factories.agent import AgentFactoryConfig
from src.core.dependencies.di_container import get_llm_service, get_agent_repository, get_agent_service
from src.core.services.vectorstore_orchestrator_service import VectorstoreOrchestratorService
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
    
@router.post("/vector-store/{store_name}")
async def create_vector_store(
    store_name: str,
    file: UploadFile = File(...),
    orchestrator: VectorstoreOrchestratorService = Depends(get_vectorstore_orchestrator)
):
    """Create a new vector store from file"""
    try:
        logger.info(f"Creating vector store '{store_name}' from file {file.filename}")
        
        # Validate file content
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=400,
                detail="Empty file content"
            )
        
        # Reset file position after validation
        await file.seek(0)
        
        # Process file and create vectorstore
        result = await orchestrator.process_file(file, store_name)
        
        return {
            "status": "success",
            "data": result,
            "message": f"Vector store '{store_name}' created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create vector store: {str(e)}"
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