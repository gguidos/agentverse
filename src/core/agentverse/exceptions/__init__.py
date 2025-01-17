"""Exceptions Module"""

class AgentVerseError(Exception):
    """Base exception class"""
    pass

class ConfigError(AgentVerseError):
    """Configuration error"""
    pass

class AgentError(AgentVerseError):
    """Agent error"""
    pass

class EnvironmentError(AgentVerseError):
    """Environment error"""
    pass

class SimulationError(AgentVerseError):
    """Simulation error"""
    pass

class TaskError(AgentVerseError):
    """Task error"""
    pass

class MessageBusError(AgentVerseError):
    """Message bus error"""
    pass

__all__ = [
    "AgentVerseError",
    "ConfigError",
    "AgentError",
    "EnvironmentError",
    "SimulationError",
    "TaskError",
    "MessageBusError"
] 