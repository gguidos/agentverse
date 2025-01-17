from fastapi import APIRouter, HTTPException, Depends
from src.core.services.tool_service import ToolService
from src.core.dependencies.di_container import get_tool_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/tools")
async def list_tools(
    tool_service: ToolService = Depends(get_tool_service)
):
    """List all available tools"""
    try:
        tools = await tool_service.list_tools()
        return {
            "status": "success",
            "data": tools,
            "message": "Tools retrieved successfully",
            "error": None
        }
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/capabilities")
async def list_capabilities(
    tool_service: ToolService = Depends(get_tool_service)
):
    """List all available agent capabilities"""
    try:
        capabilities = await tool_service.list_capabilities()
        return {
            "status": "success",
            "data": {
                "capabilities": capabilities
            },
            "message": "Capabilities retrieved successfully",
            "error": None
        }
    except Exception as e:
        logger.error(f"Error listing capabilities: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing capabilities: {str(e)}"
        )

@router.get("/tools/{tool_name}")
async def get_tool(
    tool_name: str,
    tool_service: ToolService = Depends(get_tool_service)
):
    """Get specific tool information"""
    try:
        tool = await tool_service.get_tool(tool_name)
        return {
            "status": "success",
            "data": tool,
            "message": "Tool retrieved successfully",
            "error": None
        }
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting tool: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/capabilities/{capability_name}")
async def get_capability(
    capability_name: str,
    tool_service: ToolService = Depends(get_tool_service)
):
    """Get specific capability information"""
    try:
        capability = await tool_service.get_capability(capability_name)
        return {
            "status": "success",
            "data": capability,
            "message": "Capability retrieved successfully",
            "error": None
        }
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting capability: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) 