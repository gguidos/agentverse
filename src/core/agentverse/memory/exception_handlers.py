from fastapi import Request
from fastapi.responses import JSONResponse
import logging
from src.core.agentverse.memory.exceptions import (
    MemoryException,
    MemoryStorageError,
    MemoryRetrievalError,
    VectorOperationError,
    MemoryBackendError,
    InvalidMemoryFormat,
    MemoryNotFound
)
from src.core.agentverse.memory.agent_metrics import AgentMetricsManager

logger = logging.getLogger(__name__)

def register_memory_exception_handlers(app):
    """Register memory-specific exception handlers"""
    
    @app.exception_handler(MemoryException)
    async def memory_exception_handler(request: Request, exc: MemoryException):
        """Handle base memory exceptions"""
        logger.error(f"Memory error: {exc.detail}", extra={
            "path": request.url.path,
            "status_code": exc.status_code
        })
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail,
                "error_type": exc.__class__.__name__
            }
        )

    @app.exception_handler(MemoryStorageError)
    async def memory_storage_error_handler(request: Request, exc: MemoryStorageError):
        """Handle memory storage errors"""
        logger.error(f"Memory storage error: {exc.detail}", extra={
            "path": request.url.path,
            "original_error": str(exc.original_error) if exc.original_error else None
        })
        
        # Update metrics
        AgentMetricsManager.record_memory_operation(
            agent_id="system",
            operation="store",
            status="error"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail,
                "error_type": "MemoryStorageError"
            }
        )

    @app.exception_handler(MemoryRetrievalError)
    async def memory_retrieval_error_handler(request: Request, exc: MemoryRetrievalError):
        """Handle memory retrieval errors"""
        logger.error(f"Memory retrieval error: {exc.detail}", extra={
            "path": request.url.path,
            "original_error": str(exc.original_error) if exc.original_error else None
        })
        
        # Update metrics
        AgentMetricsManager.record_memory_operation(
            agent_id="system",
            operation="retrieve",
            status="error"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail,
                "error_type": "MemoryRetrievalError"
            }
        )

    @app.exception_handler(VectorOperationError)
    async def vector_operation_error_handler(request: Request, exc: VectorOperationError):
        """Handle vector operation errors"""
        logger.error(f"Vector operation error: {exc.detail}", extra={
            "path": request.url.path,
            "original_error": str(exc.original_error) if exc.original_error else None
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail,
                "error_type": "VectorOperationError"
            }
        )

    @app.exception_handler(MemoryBackendError)
    async def memory_backend_error_handler(request: Request, exc: MemoryBackendError):
        """Handle backend service errors"""
        logger.error(f"Backend error ({exc.backend}): {exc.detail}", extra={
            "path": request.url.path,
            "backend": exc.backend,
            "original_error": str(exc.original_error) if exc.original_error else None
        })
        
        # Update health metrics
        AgentMetricsManager.update_health_status(
            agent_id="system",
            component=exc.backend,
            status=0.0
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail,
                "error_type": "MemoryBackendError",
                "backend": exc.backend
            }
        )

    @app.exception_handler(InvalidMemoryFormat)
    async def invalid_memory_format_handler(request: Request, exc: InvalidMemoryFormat):
        """Handle invalid memory format errors"""
        logger.error(f"Invalid memory format: {exc.detail}", extra={
            "path": request.url.path
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail,
                "error_type": "InvalidMemoryFormat"
            }
        )

    @app.exception_handler(MemoryNotFound)
    async def memory_not_found_handler(request: Request, exc: MemoryNotFound):
        """Handle memory not found errors"""
        logger.error(f"Memory not found: {exc.detail}", extra={
            "path": request.url.path
        })
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail,
                "error_type": "MemoryNotFound"
            }
        ) 