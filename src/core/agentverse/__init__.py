"""
AgentVerse Framework

A framework for building multi-agent systems.
"""

import logging
from typing import Dict, Type

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import core components
from src.core.agentverse.agents import BaseAgent
from src.core.agentverse.environment import BaseEnvironment
from src.core.agentverse.message import Message
from src.core.agentverse.message_bus import BaseMessageBus
from src.core.agentverse.resources import ResourceManager
from src.core.agentverse.recovery import RetryHandler
from src.core.agentverse.exceptions import AgentVerseError

# Import main class
from src.core.agentverse.agentverse import AgentVerse, AgentVerseConfig

__version__ = "0.1.0"

__all__ = [
    # Main classes
    "AgentVerse",
    "AgentVerseConfig",
    
    # Base classes
    "BaseAgent",
    "BaseEnvironment",
    "BaseMessageBus",
    
    # Core components
    "Message",
    "ResourceManager",
    "RetryHandler",
    
    # Exceptions
    "AgentVerseError",
    
    # Version
    "__version__"
] 