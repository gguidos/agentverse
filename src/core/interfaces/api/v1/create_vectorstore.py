from fastapi import APIRouter, UploadFile, File, Depends
from src.core.services.vectorstore_orchestrator_service import VectorstoreOrchestratorService
from src.core.dependencies.vectorstore_orchestrator_dependency import get_vectorstore_orchestrator

router = APIRouter()

@router.post("/vector-store/{store_name}")
async def create_vector_store(
    store_name: str,
    file: UploadFile = File(...),
    orchestrator: VectorstoreOrchestratorService = Depends(get_vectorstore_orchestrator)
):
    result = await orchestrator.process_file(file, store_name)
    return result