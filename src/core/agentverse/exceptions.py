"""
AgentVerse Exceptions Module

This module defines custom exceptions used throughout the AgentVerse framework.
"""

class AgentVerseError(Exception):
    """Base exception for all AgentVerse errors"""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

# Parser Errors
class ParserError(AgentVerseError):
    """Base class for parser-related errors"""
    pass

class ValidationParserError(ParserError):
    """Raised when parser validation fails"""
    pass

class SchemaParserError(ParserError):
    """Raised when schema validation fails"""
    pass

# Component Errors
class ComponentError(AgentVerseError):
    """Base class for component-related errors"""
    pass

class ComponentNotFoundError(ComponentError):
    """Raised when a component is not found"""
    pass

class ComponentInitError(ComponentError):
    """Raised when component initialization fails"""
    pass

# Agent Errors
class AgentError(AgentVerseError):
    """Base class for agent-related errors"""
    pass

class AgentStateError(AgentError):
    """Raised when agent state operations fail"""
    pass

class AgentConfigError(AgentError):
    """Raised when agent configuration is invalid"""
    pass

class AgentExecutionError(AgentError):
    """Raised when agent execution fails"""
    pass

class AgentCommunicationError(AgentError):
    """Raised when agent communication fails"""
    pass

# Registry Errors
class RegistryError(AgentVerseError):
    """Base class for registry-related errors"""
    pass

class RegistrationError(RegistryError):
    """Raised when registration operations fail"""
    pass

class LookupError(RegistryError):
    """Raised when registry lookups fail"""
    pass

# Memory Errors
class MemoryError(AgentVerseError):
    """Base class for memory-related errors"""
    pass

class MemoryStorageError(MemoryError):
    """Raised when storing data in memory fails"""
    pass

class MemoryRetrievalError(MemoryError):
    """Raised when retrieving data from memory fails"""
    pass

class MemoryManipulationError(MemoryError):
    """Raised when manipulating memory data fails"""
    pass

# Backend Errors
class BackendError(AgentVerseError):
    """Base class for backend-related errors"""
    pass

class VectorBackendError(BackendError):
    """Raised when vector operations fail"""
    pass

class StorageBackendError(BackendError):
    """Raised when storage operations fail"""
    pass

class DatabaseBackendError(BackendError):
    """Raised when database operations fail"""
    pass

# Service Errors
class ServiceError(AgentVerseError):
    """Base class for service-related errors"""
    pass

class LLMError(ServiceError):
    """Raised when LLM service calls fail"""
    pass

# Monitoring Errors
class MonitoringError(AgentVerseError):
    """Base class for monitoring-related errors"""
    pass

class MetricsError(MonitoringError):
    """Raised when metrics collection fails"""
    pass

class AlertError(MonitoringError):
    """Raised when alert processing fails"""
    pass

class TraceError(MonitoringError):
    """Raised when trace collection fails"""
    pass

# Operation Errors
class ActionError(AgentVerseError):
    """Raised when an agent action fails"""
    pass

class MessageBusError(AgentVerseError):
    """Raised when message bus operations fail"""
    pass

class ConfigError(AgentVerseError):
    """Raised when configuration is invalid"""
    pass

class ValidationError(AgentVerseError):
    """Raised when validation fails"""
    pass

class ResourceError(AgentVerseError):
    """Raised when resource limits are exceeded"""
    pass

class StateError(AgentVerseError):
    """Raised when state operations fail"""
    pass

class EnvironmentError(AgentVerseError):
    """Raised when environment operations fail"""
    pass

class TaskError(AgentVerseError):
    """Raised when task operations fail"""
    pass

class ToolError(AgentVerseError):
    """Raised when tool operations fail"""
    pass

# Security Errors
class SecurityError(AgentVerseError):
    """Base class for security-related errors"""
    pass

class AuthenticationError(SecurityError):
    """Raised when authentication fails"""
    pass

class AuthorizationError(SecurityError):
    """Raised when authorization fails"""
    pass

# Rate Limiting Errors
class RateLimitError(ResourceError):
    """Raised when rate limits are exceeded"""
    pass

class TimeoutError(AgentVerseError):
    """Raised when operations timeout"""
    pass

__all__ = [
    # Base
    "AgentVerseError",
    
    # Parser
    "ParserError",
    "ValidationParserError",
    "SchemaParserError",
    
    # Component
    "ComponentError",
    "ComponentNotFoundError",
    "ComponentInitError",
    
    # Agent
    "AgentError",
    "AgentStateError",
    "AgentConfigError",
    "AgentExecutionError",
    "AgentCommunicationError",
    
    # Registry
    "RegistryError",
    "RegistrationError",
    "LookupError",
    
    # Memory
    "MemoryError",
    "MemoryStorageError",
    "MemoryRetrievalError",
    "MemoryManipulationError",
    
    # Backend
    "BackendError",
    "VectorBackendError",
    "StorageBackendError",
    "DatabaseBackendError",
    
    # Service
    "ServiceError",
    "LLMError",
    
    # Monitoring
    "MonitoringError",
    "MetricsError",
    "AlertError",
    "TraceError",
    
    # Operation
    "ActionError",
    "MessageBusError",
    "ConfigError",
    "ValidationError",
    "ResourceError",
    "StateError",
    "EnvironmentError",
    "TaskError",
    "ToolError",
    
    # Security
    "SecurityError",
    "AuthenticationError",
    "AuthorizationError",
    
    # Rate Limiting
    "RateLimitError",
    "TimeoutError"
] 