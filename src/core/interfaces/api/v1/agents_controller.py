from fastapi import APIRouter, UploadFile, File, Depends
from src.core.services.vectorstore_orchestrator_service import VectorstoreOrchestratorService
from src.core.dependencies.vectorstore_orchestrator_dependency import get_vectorstore_orchestrator
from src.core.dependencies.di_container import Container
from src.core.dependencies.api_key_dependency import get_api_key
import logging

router = APIRouter()
# Initialize the logger
logger = logging.getLogger(__name__)

# Get configuration from the container to conditionally include dependencies
container = Container()

# Conditionally add API key protection based on environment
api_key_dependency = Depends(get_api_key) if container.config.environment() != "development" else None

@router.post("/agents")
async def create_agents():
    # Create agents logic here (if any)
    logger.info("Creating agents")
    agents_data = {"message": "agents created"}  # Example data to return
    return {"status": "success", "data": agents_data}  # Correctly return the data

@router.post("/vector-store/{store_name}")
async def create_vector_store(
    store_name: str,
    file: UploadFile = File(...),
    orchestrator: VectorstoreOrchestratorService = Depends(get_vectorstore_orchestrator)
):
    logger.info("Creating vector store")
    result = await orchestrator.process_file(file, store_name)
    return result