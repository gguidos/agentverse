from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from pydantic import BaseModel
import logging
import uuid
from datetime import datetime

from src.core.agentverse.factories import AgentFactory
from src.core.agentverse.factories.agent import AgentFactoryConfig
from src.core.dependencies.di_container import get_llm_service, get_agent_repository
from src.core.services.vectorstore_orchestrator_service import VectorstoreOrchestratorService
from src.core.dependencies.vectorstore_orchestrator_dependency import get_vectorstore_orchestrator
from src.core.repositories.agent_repository import AgentRepository

router = APIRouter()
logger = logging.getLogger(__name__)

class CreateAgentRequest(BaseModel):
    """Request model for agent creation"""
    name: str
    type: str = "assistant"
    capabilities: list = []
    llm_config: Dict[str, Any] = {"type": "mock"}
    metadata: Dict[str, Any] = {}

@router.post("/agents")
async def create_agents(
    request: CreateAgentRequest,
    llm_service = Depends(get_llm_service),
    agent_repository: AgentRepository = Depends(get_agent_repository)
):
    """Create a new agent"""
    try:
        # Create agent config with generated ID
        config = AgentFactoryConfig(
            id=str(uuid.uuid4()),
            type=request.type,
            name=request.name,
            capabilities=request.capabilities,
            llm=request.llm_config,
            metadata=request.metadata
        )

        # Create agent using factory
        agent = await AgentFactory.create(
            config=config,
            llm_service=llm_service
        )

        # Store agent in database
        agent_data = {
            "id": agent.config.id,
            "name": agent.config.name,
            "type": agent.config.type,
            "capabilities": agent.config.capabilities,
            "metadata": agent.config.metadata,
            "created_at": datetime.utcnow()
        }
        await agent_repository.create(agent_data)

        # Return agent data
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