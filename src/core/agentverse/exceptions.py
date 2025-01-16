"""
AgentVerse Exceptions Module

This module defines custom exceptions used throughout AgentVerse.
"""

class AgentVerseError(Exception):
    """Base exception for AgentVerse errors"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

# Backend Errors
class BackendError(AgentVerseError):
    """Base backend error"""
    pass

class VectorBackendError(BackendError):
    """Vector backend error"""
    pass

class StorageBackendError(BackendError):
    """Storage backend error"""
    pass

class DatabaseBackendError(BackendError):
    """Database backend error"""
    pass

# Memory Errors
class MemoryError(AgentVerseError):
    """Memory error"""
    pass

class MemoryManipulationError(MemoryError):
    """Memory manipulation error"""
    pass

class MemoryStorageError(MemoryError):
    """Memory storage error"""
    pass

class MemoryRetrievalError(MemoryError):
    """Memory retrieval error"""
    pass

# Service Errors
class LLMError(AgentVerseError):
    """LLM service error"""
    pass

class AgentError(AgentVerseError):
    """Agent error"""
    pass

class EvaluationError(AgentVerseError):
    """Evaluation error"""
    pass

# System Errors
class ConfigError(AgentVerseError):
    """Configuration error"""
    pass

class MessageBusError(AgentVerseError):
    """Message bus error"""
    pass

class ValidationError(AgentVerseError):
    """Validation error"""
    pass

# Security Errors
class AuthenticationError(AgentVerseError):
    """Authentication error"""
    pass

class AuthorizationError(AgentVerseError):
    """Authorization error"""
    pass

# Operation Errors
class RateLimitError(AgentVerseError):
    """Rate limit error"""
    pass

class TimeoutError(AgentVerseError):
    """Timeout error"""
    pass

class NotFoundError(AgentVerseError):
    """Resource not found error"""
    pass

class DuplicateError(AgentVerseError):
    """Duplicate resource error"""
    pass

# Error registry
ERROR_TYPES = {
    # Backend errors
    'backend': BackendError,
    'vector_backend': VectorBackendError,
    'storage_backend': StorageBackendError,
    'database_backend': DatabaseBackendError,
    
    # Memory errors
    'memory': MemoryError,
    'memory_manipulation': MemoryManipulationError,
    'memory_storage': MemoryStorageError,
    'memory_retrieval': MemoryRetrievalError,
    
    # Service errors
    'llm': LLMError,
    'agent': AgentError,
    'evaluation': EvaluationError,
    
    # System errors
    'config': ConfigError,
    'message_bus': MessageBusError,
    'validation': ValidationError,
    
    # Security errors
    'auth': AuthenticationError,
    'authorization': AuthorizationError,
    
    # Operation errors
    'rate_limit': RateLimitError,
    'timeout': TimeoutError,
    'not_found': NotFoundError,
    'duplicate': DuplicateError
}

def create_error(
    type: str,
    message: str,
    details: dict = None
) -> AgentVerseError:
    """Create error of specified type
    
    Args:
        type: Error type
        message: Error message
        details: Optional error details
        
    Returns:
        Error instance
        
    Raises:
        ValueError: If type is invalid
    """
    if type not in ERROR_TYPES:
        raise ValueError(f"Invalid error type: {type}")
        
    error_class = ERROR_TYPES[type]
    return error_class(message, details) 