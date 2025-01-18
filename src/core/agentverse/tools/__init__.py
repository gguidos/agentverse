"""
AgentVerse Tools Module

This module provides various tools for agent use.
"""

from .base import (
    BaseTool,
    ToolConfig,
    ToolResult,
    ToolError,
    ToolExecutionError,
    ToolAuthenticationError,
    ToolPermissionError,
    ToolValidationError,
    ToolDependencyError
)

from .registry import tool_registry, ToolRegistry
from .types import (
    AgentCapability,
    ToolType,
    SIMPLE_TOOLS,
    COMPLEX_TOOLS
)
from .capabilities import register_default_tools

# Tools are now registered via decorators, no need for initialization

__all__ = [
    'BaseTool',
    'ToolConfig',
    'ToolResult',
    'tool_registry',
    'ToolRegistry',
    'AgentCapability',
    'ToolType',
    'SIMPLE_TOOLS',
    'COMPLEX_TOOLS',
    'register_default_tools',
    # Error classes
    'ToolError',
    'ToolExecutionError',
    'ToolAuthenticationError',
    'ToolPermissionError',
    'ToolValidationError',
    'ToolDependencyError'
] 