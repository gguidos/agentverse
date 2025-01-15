from src.core.services.check_duplicate import CheckDuplicateService
from fastapi import Depends
from dependency_injector.wiring import inject, Provide
from src.core.dependencies.di_container import Container

@inject
async def get_check_duplicate() -> CheckDuplicateService:
    """Dependency provider for CheckDuplicateService"""
    return Container.check_duplicate_service()