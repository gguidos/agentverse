from src.core.interfaces.api.v1.health_check import router as health_check_router
from src.app.interfaces.api.v1.controller import router as controller_router
from src.core.interfaces.api.v1.agents_controller import router as agents_router
from src.core.interfaces.api.v1.simulation_controller import router as simulation_router
from src.core.infrastructure.metrics import metrics_router
from src.core.interfaces.api.v1.tools_controller import router as tools_router
from src.core.interfaces.api.v1.environments_controller import router as environments_router
from src.core.interfaces.api.v1.environment_orchestration_controller import router as env_orchestration_router
from src.core.interfaces.api.v1.orchestrator_controller import router as orchestrator_router
from src.core.interfaces.api.v1.vectorstore_controller import router as vectorstore_router

def register_routers(app, container):
    # Wire the container to the modules that use the dependencies
    container.wire(modules=[
        "src.app.interfaces.api.v1.controller",
        "src.core.interfaces.api.v1.agents_controller",
        "src.core.interfaces.api.v1.simulation_controller",
        "src.core.interfaces.api.v1.vectorstore_controller"
    ])

    # Include routers
    app.include_router(health_check_router, prefix="/api/v1")
    app.include_router(controller_router, prefix="/api/v1", tags=["users"])
    app.include_router(agents_router, prefix="/api/v1", tags=["agents"])
    app.include_router(simulation_router, prefix="/api/v1", tags=["simulation"])
    app.include_router(metrics_router, prefix="/internal", tags=["monitoring"])
    app.include_router(tools_router, prefix="/api/v1", tags=["tools"])
    app.include_router(environments_router, prefix="/api/v1", tags=["environments"])
    app.include_router(env_orchestration_router, prefix="/api/v1", tags=["environment-orchestration"])
    app.include_router(orchestrator_router, prefix="/api/v1", tags=["orchestrator"])
    app.include_router(vectorstore_router, prefix="/api/v1", tags=["vectorstore"])