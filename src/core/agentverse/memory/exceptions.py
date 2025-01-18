from fastapi import HTTPException
from typing import Optional, Any

class MemoryException(HTTPException):
    """Base exception for memory-related errors"""
    def __init__(self, detail: str, status_code: int = 500):
        super().__init__(status_code=status_code, detail=detail)

class MemoryStorageError(Exception):
    """Base exception for memory storage errors"""
    def __init__(self, message: str = "Memory storage error occurred"):
        self.message = message
        super().__init__(self.message)

class MemoryRetrievalError(MemoryException):
    """Raised when memory retrieval operations fail"""
    def __init__(self, detail: str, original_error: Optional[Exception] = None):
        super().__init__(
            detail=f"Memory retrieval error: {detail}",
            status_code=500
        )
        self.original_error = original_error

class VectorOperationError(MemoryException):
    """Raised when vector operations fail"""
    def __init__(self, detail: str, original_error: Optional[Exception] = None):
        super().__init__(
            detail=f"Vector operation error: {detail}",
            status_code=500
        )
        self.original_error = original_error

class MemoryBackendError(MemoryException):
    """Raised when memory backend (Redis/MongoDB) operations fail"""
    def __init__(self, backend: str, detail: str, original_error: Optional[Exception] = None):
        super().__init__(
            detail=f"{backend} backend error: {detail}",
            status_code=503
        )
        self.backend = backend
        self.original_error = original_error

class InvalidMemoryFormat(MemoryException):
    """Raised when memory data format is invalid"""
    def __init__(self, detail: str):
        super().__init__(
            detail=f"Invalid memory format: {detail}",
            status_code=400
        )

class MemoryNotFound(MemoryException):
    """Raised when requested memory is not found"""
    def __init__(self, memory_id: Any):
        super().__init__(
            detail=f"Memory not found: {memory_id}",
            status_code=404
        ) 