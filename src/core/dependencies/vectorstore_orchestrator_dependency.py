from fastapi import Depends
from dependency_injector.wiring import inject, Provide
from src.core.services.vectorstore_orchestrator_service import VectorstoreOrchestratorService
from src.core.dependencies.di_container import Container

@inject
async def get_vectorstore_orchestrator() -> VectorstoreOrchestratorService:
    """Dependency provider for VectorstoreOrchestratorService"""
    return Container.vectorstore_orchestrator_service()