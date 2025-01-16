"""
AgentVerse Message Bus Module

This module provides message bus implementations for agent communication.
It includes different message bus backends and common messaging patterns.

Key Components:
    - BaseMessageBus: Abstract base class for message buses
    - RedisMessageBus: Redis-based message bus implementation
    - InMemoryMessageBus: In-memory message bus for testing
    - MessageTypes: Enumeration of message types
"""

import logging
from enum import Enum
from typing import Optional, Type

from src.core.agentverse.message_bus.base import BaseMessageBus
from src.core.agentverse.message_bus.redis import RedisMessageBus  # Updated name
from src.core.agentverse.message_bus.memory import InMemoryMessageBus
from src.core.agentverse.exceptions import MessageBusError

logger = logging.getLogger(__name__)

class MessageTypes(str, Enum):
    """Message type enumeration"""
    COMMAND = "command"
    EVENT = "event"
    RESPONSE = "response"
    ERROR = "error"

class MessageBusType(str, Enum):
    """Message bus type enumeration"""
    REDIS = "redis"
    MEMORY = "memory"

def create_message_bus(
    bus_type: MessageBusType,
    **kwargs
) -> BaseMessageBus:
    """Create message bus instance
    
    Args:
        bus_type: Type of message bus to create
        **kwargs: Additional configuration arguments
        
    Returns:
        Configured message bus instance
        
    Raises:
        MessageBusError: If creation fails
    """
    bus_classes: dict[MessageBusType, Type[BaseMessageBus]] = {
        MessageBusType.REDIS: RedisMessageBus,
        MessageBusType.MEMORY: InMemoryMessageBus
    }
    
    try:
        bus_class = bus_classes[bus_type]
        return bus_class(**kwargs)
    except KeyError:
        raise MessageBusError(f"Unknown message bus type: {bus_type}")
    except Exception as e:
        raise MessageBusError(f"Failed to create message bus: {str(e)}")

__all__ = [
    "BaseMessageBus",
    "RedisMessageBus",
    "InMemoryMessageBus",
    "MessageTypes",
    "MessageBusType",
    "create_message_bus"
]

# Version
__version__ = "1.0.0" 