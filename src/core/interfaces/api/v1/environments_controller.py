from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging
from src.core.services.environment_service import EnvironmentService
from src.core.dependencies.di_container import get_environment_service

router = APIRouter()
logger = logging.getLogger(__name__)

class CreateEnvironmentRequest(BaseModel):
    name: str
    description: str
    config: Dict[str, Any] = {}
    enabled_capabilities: list = []
    metadata: Dict[str, Any] = {}

class UpdateEnvironmentRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    enabled_capabilities: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/environments")
async def create_environment(
    request: CreateEnvironmentRequest,
    environment_service: EnvironmentService = Depends(get_environment_service)
):
    """Create a new environment"""
    try:
        environment = await environment_service.create_environment(request.model_dump())
        return {
            "status": "success",
            "data": environment,
            "message": "Environment created successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating environment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/environments")
async def list_environments(
    environment_service: EnvironmentService = Depends(get_environment_service)
):
    """List all environments"""
    try:
        result = await environment_service.list_environments()
        return {
            "status": "success",
            "data": result,
            "message": "Environments retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error listing environments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/environments/{environment_id}")
async def get_environment(
    environment_id: str,
    environment_service: EnvironmentService = Depends(get_environment_service)
):
    """Get environment by ID"""
    try:
        environment = await environment_service.get_environment(environment_id)
        return {
            "status": "success",
            "data": environment,
            "message": "Environment retrieved successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting environment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/environments/{environment_id}")
async def update_environment(
    environment_id: str,
    request: UpdateEnvironmentRequest,
    environment_service: EnvironmentService = Depends(get_environment_service)
):
    """Update environment"""
    try:
        environment = await environment_service.update_environment(
            environment_id,
            request.model_dump(exclude_unset=True)
        )
        return {
            "status": "success",
            "data": environment,
            "message": "Environment updated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating environment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/environments/{environment_id}")
async def delete_environment(
    environment_id: str,
    environment_service: EnvironmentService = Depends(get_environment_service)
):
    """Delete environment"""
    try:
        deleted = await environment_service.delete_environment(environment_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Environment not found")
        return {
            "status": "success",
            "data": None,
            "message": "Environment deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting environment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 