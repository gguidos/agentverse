from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging
from src.core.services.environment_service import EnvironmentService
from src.core.dependencies.di_container import get_environment_service

router = APIRouter()
logger = logging.getLogger(__name__)

class ExecuteRequest(BaseModel):
    """Request model for environment execution"""
    input: Dict[str, Any]
    async_execution: bool = False
    timeout: Optional[float] = None

@router.post("/environments/{environment_id}/activate")
async def activate_environment(
    environment_id: str,
    environment_service: EnvironmentService = Depends(get_environment_service)
):
    """Activate an environment and initialize its resources"""
    try:
        result = await environment_service.activate_environment(environment_id)
        return {
            "status": "success",
            "data": result,
            "message": "Environment activated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error activating environment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/environments/{environment_id}/deactivate")
async def deactivate_environment(
    environment_id: str,
    environment_service: EnvironmentService = Depends(get_environment_service)
):
    """Deactivate an environment and cleanup resources"""
    try:
        result = await environment_service.deactivate_environment(environment_id)
        return {
            "status": "success",
            "data": result,
            "message": "Environment deactivated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deactivating environment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/environments/{environment_id}/execute")
async def execute_environment(
    environment_id: str,
    request: ExecuteRequest,
    background_tasks: BackgroundTasks,
    environment_service: EnvironmentService = Depends(get_environment_service)
):
    """Execute operations in the environment"""
    try:
        if request.async_execution:
            # Start async execution
            background_tasks.add_task(
                environment_service.execute_environment,
                environment_id,
                request.input,
                request.timeout
            )
            return {
                "status": "success",
                "data": {"execution_status": "started"},
                "message": "Environment execution started"
            }
        else:
            # Execute synchronously
            result = await environment_service.execute_environment(
                environment_id,
                request.input,
                request.timeout
            )
            return {
                "status": "success",
                "data": result,
                "message": "Environment execution completed"
            }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing environment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/environments/{environment_id}/status")
async def get_environment_status(
    environment_id: str,
    environment_service: EnvironmentService = Depends(get_environment_service)
):
    """Get environment execution status"""
    try:
        status = await environment_service.get_environment_status(environment_id)
        return {
            "status": "success",
            "data": status,
            "message": "Environment status retrieved"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting environment status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 