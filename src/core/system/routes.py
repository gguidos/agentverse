from src.core.interfaces.api.v1.health_check import router as health_check_router
from src.app.interfaces.api.v1.controller import router as controller_router
from src.core.interfaces.api.v1.agents_controller import router as agents_router
from src.core.infrastructure.metrics import metrics_router

def register_routers(app, container):
    # Wire the container to the modules that use the dependencies
    container.wire(modules=[
        "src.app.interfaces.api.v1.controller",
        "src.core.interfaces.api.v1.agents_controller"
    ])  # Wire the user controller
    # Include health check routes
    app.include_router(health_check_router, prefix="/api/v1")

    # Include the user router with dependency injection configured
    app.include_router(controller_router, prefix="/api/v1", tags=["users"])
    app.include_router(agents_router, prefix="/api/v1", tags=["agents"])
    
    # Add metrics router without prefix to match Prometheus configuration
    app.include_router(metrics_router, prefix="/internal", tags=["monitoring"])
