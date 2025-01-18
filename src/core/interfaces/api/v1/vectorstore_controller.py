from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from src.core.services.vectorstore_service import VectorstoreService
from src.core.dependencies.vectorstore_orchestrator_dependency import get_vectorstore_orchestrator
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/vector-store/{store_name}", tags=["vectorstore"])
async def create_vector_store(
    store_name: str,
    file: UploadFile = File(...),
    orchestrator: VectorstoreService = Depends(get_vectorstore_orchestrator)
):
    """Create a new vector store from file"""
    try:
        logger.info(f"Creating vector store '{store_name}' from file {file.filename}")
        logger.debug(f"Orchestrator instance: {orchestrator}")
        
        result = await orchestrator.process_file(file, store_name)
        logger.debug(f"Process result: {result}")
        
        return {
            "status": "success",
            "data": result,
            "message": f"Vectorstore '{store_name}' created successfully"
        }
        
    except HTTPException as he:
        logger.error(f"HTTP Exception in create_vector_store: {str(he)}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create vector store: {str(e)}"
        )

@router.get("/vector-store", tags=["vectorstore"])
async def list_vectorstores(
    orchestrator: VectorstoreService = Depends(get_vectorstore_orchestrator)
) -> Dict[str, Any]:
    """List all vector stores"""
    try:
        stores = await orchestrator.list_stores()
        logger.info(f"Controller - Found stores: {stores}")
        return {
            "status": "success",
            "data": stores,
            "message": "Vector stores retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error listing vector stores: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list vector stores: {str(e)}"
        )

@router.get("/vector-store/{store_name}", tags=["vectorstore"])
async def get_vector_store(
    store_name: str,
    orchestrator: VectorstoreService = Depends(get_vectorstore_orchestrator)
):
    """Get details about a specific vector store"""
    try:
        logger.info(f"Getting vector store details for {store_name}")
        store_details = await orchestrator.get_store_details(store_name)
        return {
            "status": "success",
            "data": store_details,
            "message": None
        }
    except Exception as e:
        logger.error(f"Error getting vector store details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get vector store details: {str(e)}"
        ) 