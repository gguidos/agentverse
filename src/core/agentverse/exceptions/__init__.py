"""AgentVerse exceptions module"""

class AgentVerseError(Exception):
    """Base exception for AgentVerse"""
    pass

class ConfigError(AgentVerseError):
    """Configuration error"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

class RegistrationError(AgentVerseError):
    """Raised when registration fails"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

class ComponentNotFoundError(AgentVerseError):
    """Raised when a component is not found"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

class ParserError(AgentVerseError):
    """Raised when parsing fails"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

class LLMError(AgentVerseError):
    """Raised when LLM operations fail"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

class SimulationError(AgentVerseError):
    """Raised when simulation fails"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

class MemoryManipulationError(AgentVerseError):
    """Raised when memory manipulation fails"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

class AgentError(AgentVerseError):
    """Raised when agent operations fail"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

class ActionError(AgentVerseError):
    """Raised when action execution fails"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

class AgentStateError(AgentVerseError):
    """Raised when agent state operations fail"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

class EnvironmentError(AgentVerseError):
    """Environment error"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

class MemoryError(AgentVerseError):
    """Memory operation error"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

class MemoryStorageError(AgentVerseError):
    """Memory storage error"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

class MessageBusError(AgentVerseError):
    """Message bus error"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}

__all__ = [
    "AgentVerseError",
    "ConfigError",
    "RegistrationError",
    "ComponentNotFoundError",
    "ParserError",
    "LLMError",
    "SimulationError",
    "MemoryManipulationError",
    "AgentError",
    "ActionError",
    "AgentStateError",
    "EnvironmentError",
    "MemoryError",
    "MemoryStorageError",
    "MessageBusError"
] 