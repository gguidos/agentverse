"""
AgentVerse Agent Mixins Module

This module provides reusable mixins that add specific capabilities to agents.
These mixins can be combined with agent classes to extend their functionality
in a modular way.

Key Components:
    - MemoryHandlerMixin: Adds memory management capabilities
    - MessageHandlerMixin: Adds message handling and routing capabilities

Example Usage:
    >>> from src.core.agentverse.agents.mixins import MemoryHandlerMixin, MessageHandlerMixin
    >>> 
    >>> class MyAgent(BaseAgent, MemoryHandlerMixin, MessageHandlerMixin):
    ...     def __init__(self, memory, *args, **kwargs):
    ...         BaseAgent.__init__(self, *args, **kwargs)
    ...         MemoryHandlerMixin.__init__(self, memory)
    ...         MessageHandlerMixin.__init__(self)
    >>> 
    >>> # Use mixin capabilities
    >>> await agent.remember(message)
    >>> await agent.dispatch_message(message)
"""

from src.core.agentverse.agents.mixins.memory_handler import (
    MemoryHandlerMixin
)

from src.core.agentverse.agents.mixins.message_handler import (
    MessageHandlerMixin
)

__all__ = [
    "MemoryHandlerMixin",
    "MessageHandlerMixin"
] 