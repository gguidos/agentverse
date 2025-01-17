from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import logging
from src.core.services.environment_service import EnvironmentService
from src.core.dependencies.di_container import get_environment_service
from .models.orchestrator import OrchestratorConfigRequest

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/environments/{environment_id}/orchestrator")
async def configure_orchestrator(
    environment_id: str,
    config: OrchestratorConfigRequest,
    environment_service: EnvironmentService = Depends(get_environment_service)
):
    """Configure orchestrator for an environment"""
    try:
        result = await environment_service.configure_orchestrator(environment_id, config.model_dump())
        return {
            "status": "success",
            "data": result,
            "message": "Orchestrator configured successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error configuring orchestrator: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/environments/{environment_id}/orchestrator/roles")
async def list_agent_roles(
    environment_id: str,
    environment_service: EnvironmentService = Depends(get_environment_service)
):
    """List configured agent roles"""
    try:
        roles = await environment_service.get_orchestrator_roles(environment_id)
        return {
            "status": "success",
            "data": roles,
            "message": "Agent roles retrieved successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing agent roles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/environments/{environment_id}/orchestrator/roles/{role_name}")
async def add_agent_role(
    environment_id: str,
    role_name: str,
    role_config: AgentRoleConfig,
    environment_service: EnvironmentService = Depends(get_environment_service)
):
    """Add or update an agent role"""
    try:
        result = await environment_service.add_orchestrator_role(
            environment_id, 
            role_name, 
            role_config.model_dump()
        )
        return {
            "status": "success",
            "data": result,
            "message": f"Agent role '{role_name}' configured successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error configuring agent role: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 