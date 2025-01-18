"""
AgentVerse Exceptions Module

This module defines custom exceptions used throughout the AgentVerse system.
"""

class AgentVerseError(Exception):
    """Base exception for all AgentVerse errors"""
    pass

class ConfigurationError(AgentVerseError):
    """Raised when there is an error in configuration"""
    
    def __init__(self, message: str, config_key: str = None, details: dict = None):
        self.message = message
        self.config_key = config_key
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self):
        error_msg = self.message
        if self.config_key:
            error_msg = f"{error_msg} (key: {self.config_key})"
        if self.details:
            error_msg = f"{error_msg} - details: {self.details}"
        return error_msg

# Backwards compatibility
ConfigError = ConfigurationError

# Registry Exceptions
class RegistrationError(AgentVerseError):
    """Raised when there is an error registering components"""
    pass

class ComponentNotFoundError(AgentVerseError):
    """Raised when a requested component is not found in registry"""
    pass

# Validation Exceptions
class ValidationError(AgentVerseError):
    """Raised when validation fails"""
    pass

# Agent Exceptions
class AgentError(AgentVerseError):
    """Raised when there is an error with an agent"""
    pass

class AgentStateError(AgentError):
    """Raised when there is an error with agent state"""
    pass

# Tool Exceptions
class ToolError(AgentVerseError):
    """Raised when there is an error with a tool"""
    pass

# Memory Exceptions
class MemoryError(AgentVerseError):
    """Base exception for memory-related errors"""
    pass

class MemoryStorageError(MemoryError):
    """Raised when there is an error with memory storage operations"""
    pass

class MemoryManipulationError(MemoryError):
    """Raised when there is an error manipulating memory contents"""
    pass

# LLM Exceptions
class LLMError(AgentVerseError):
    """Raised when there is an error with LLM operations"""
    pass

# Parser Exceptions
class ParserError(AgentVerseError):
    """Raised when there is an error parsing content"""
    pass

# Communication Exceptions
class MessageBusError(AgentVerseError):
    """Raised when there is an error with message bus operations"""
    pass

# Factory Exceptions
class FactoryError(AgentVerseError):
    """Raised when there is an error in factory operations"""
    pass

# Environment Exceptions
class EnvironmentError(AgentVerseError):
    """Raised when there is an error with the environment"""
    pass

# Action Exceptions
class ActionError(AgentVerseError):
    """Raised when there is an error executing an action"""
    pass

class ActionValidationError(ActionError):
    """Raised when action validation fails"""
    pass

class ActionExecutionError(ActionError):
    """Raised when action execution fails"""
    pass

# Simulation Exceptions
class SimulationError(AgentVerseError):
    """Raised when there is an error in simulation execution"""
    pass

class SimulationStateError(SimulationError):
    """Raised when there is an error with simulation state"""
    pass

class SimulationConfigError(SimulationError):
    """Raised when there is an error with simulation configuration"""
    pass

# Export all exception classes
__all__ = [
    "AgentVerseError",
    "ConfigurationError",
    "ConfigError",
    "RegistrationError",
    "ComponentNotFoundError",
    "ValidationError",
    "AgentError",
    "AgentStateError",
    "ActionError",
    "ActionValidationError",
    "ActionExecutionError",
    "ToolError",
    "MemoryError",
    "MemoryStorageError",
    "MemoryManipulationError",
    "LLMError",
    "ParserError",
    "MessageBusError",
    "FactoryError",
    "EnvironmentError",
    "SimulationError",
    "SimulationStateError",
    "SimulationConfigError"
] 