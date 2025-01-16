"""Message Types Module"""

from enum import Enum, auto
from typing import Dict, Any, Optional

class MessageTypes(Enum):
    """Enumeration of message types"""
    
    # Core message types
    COMMAND = auto()
    EVENT = auto()
    QUERY = auto()
    RESPONSE = auto()
    
    # System message types
    HEARTBEAT = auto()
    STATUS = auto()
    ERROR = auto()
    
    # Agent message types
    TASK = auto()
    RESULT = auto()
    STATE = auto()
    
    # Control message types
    START = auto()
    STOP = auto()
    PAUSE = auto()
    RESUME = auto()
    
    # Communication message types
    REQUEST = auto()
    REPLY = auto()
    BROADCAST = auto()
    NOTIFICATION = auto()

    def __str__(self) -> str:
        return self.name.lower()

    @classmethod
    def from_str(cls, type_str: str) -> "MessageTypes":
        """Convert string to message type
        
        Args:
            type_str: String representation of message type
            
        Returns:
            MessageTypes enum value
            
        Raises:
            ValueError: If string doesn't match any type
        """
        try:
            return cls[type_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid message type: {type_str}") 