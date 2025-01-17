"""Exceptions for AgentVerse"""

class AgentVerseError(Exception):
    """Base exception for AgentVerse"""
    pass

class ConfigError(AgentVerseError):
    """Configuration error"""
    pass

class AgentError(AgentVerseError):
    """Agent error"""
    pass

class SimulationError(AgentVerseError):
    """Simulation error"""
    pass

class EnvironmentError(AgentVerseError):
    """Environment error"""
    pass

class MemoryError(AgentVerseError):
    """Memory operation error"""
    pass

class MemoryStorageError(AgentVerseError):
    """Memory storage error"""
    pass

class MessageBusError(AgentVerseError):
    """Message bus error"""
    pass

__all__ = [
    "AgentVerseError",
    "ConfigError",
    "AgentError",
    "SimulationError",
    "EnvironmentError",
    "MemoryError",
    "MemoryStorageError",
    "MessageBusError"
] 