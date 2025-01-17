"""AgentVerse exceptions"""

from typing import Optional, Dict, Any

class AgentVerseError(Exception):
    """Base exception for AgentVerse errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class ConfigError(AgentVerseError):
    """Configuration error"""
    pass

class LLMError(AgentVerseError):
    """LLM operation error"""
    pass

class RegistrationError(AgentVerseError):
    """Registration error"""
    pass

class ComponentNotFoundError(AgentVerseError):
    """Component not found error"""
    pass

class ParserError(AgentVerseError):
    """Parser error"""
    pass

class ActionError(AgentVerseError):
    """Action execution error"""
    pass

class AgentStateError(AgentVerseError):
    """Agent state error"""
    pass

class SimulationError(AgentVerseError):
    """Simulation execution error"""
    pass

class EnvironmentError(AgentVerseError):
    """Environment error"""
    pass

class ToolError(AgentVerseError):
    """Exception raised by tools during execution"""
    pass

class MessageBusError(AgentVerseError):
    """Exception raised by message bus operations"""
    pass

class AgentError(AgentVerseError):
    """Exception raised by agent operations"""
    pass

class FactoryError(AgentVerseError):
    """Exception raised during object creation"""
    pass

class MemoryError(AgentVerseError):
    """Memory operation error"""
    pass

class MemoryStorageError(AgentVerseError):
    """Memory storage error"""
    pass

class MemoryManipulationError(AgentVerseError):
    """Memory manipulation error"""
    pass

__all__ = [
    "AgentVerseError",
    "ConfigError",
    "LLMError",
    "RegistrationError",
    "ComponentNotFoundError",
    "ParserError",
    "ActionError",
    "AgentStateError",
    "SimulationError",
    "EnvironmentError",
    "ToolError",
    "MessageBusError",
    "AgentError",
    "FactoryError",
    "MemoryError",
    "MemoryStorageError",
    "MemoryManipulationError"
] 