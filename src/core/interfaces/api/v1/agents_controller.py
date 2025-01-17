from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from pydantic import BaseModel
import logging
import uuid
from datetime import datetime

from src.core.agentverse.factories import AgentFactory
from src.core.agentverse.factories.agent import AgentFactoryConfig
from src.core.dependencies.di_container import get_llm_service, get_agent_repository, get_agent_service
from src.core.services.vectorstore_orchestrator_service import VectorstoreOrchestratorService
from src.core.dependencies.vectorstore_orchestrator_dependency import get_vectorstore_orchestrator
from src.core.repositories.agent_repository import AgentRepository
from src.core.services.agent_service import AgentService

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
async def create_agents(
    request: CreateAgentRequest,
    llm_service = Depends(get_llm_service),
    agent_service: AgentService = Depends(get_agent_service)
):
    """Create a new agent"""
    try:
        config = AgentFactoryConfig(
            id=str(uuid.uuid4()),
            type=request.type,
            name=request.name,
            capabilities=request.capabilities,
            llm=request.llm_config,
            metadata=request.metadata
        )
        
        agent = await agent_service.create_agent(config, llm_service)
        
        return {
            "status": "success",
            "data": {
                "id": agent.config.id,
                "name": agent.config.name,
                "type": agent.config.type,
                "capabilities": agent.config.capabilities
            }
        }
    except ValueError as e:
        logger.error(f"Invalid agent configuration: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent configuration: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error creating agent: {str(e)}"
        )

@router.post("/vector-store/{store_name}")
async def create_vector_store(
    store_name: str,
    file: UploadFile = File(...),
    orchestrator: VectorstoreOrchestratorService = Depends(get_vectorstore_orchestrator)
):
    logger.info("Creating vector store")
    result = await orchestrator.process_file(file, store_name)
    return result

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

@router.get("/tools")
async def list_tools(
    agent_service: AgentService = Depends(get_agent_service)
):
    """List all available tools"""
    try:
        tools = await agent_service.list_tools()
        return {
            "status": "success",
            "data": {
                "tools": tools
            }
        }
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing tools: {str(e)}"
        )