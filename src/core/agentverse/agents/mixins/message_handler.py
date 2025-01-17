from typing import Dict, Any, Optional, List, Callable
import logging

from src.core.agentverse.message import Message

logger = logging.getLogger(__name__)

class MessageHandlerMixin:
    """Mixin for message handling capabilities"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def register_handler(
        self,
        message_type: str,
        handler: Callable
    ) -> None:
        """Register message handler
        
        Args:
            message_type: Type of message to handle
            handler: Handler function
        """
        if message_type not in self._handlers:
            self._handlers[message_type] = []
        self._handlers[message_type].append(handler)
    
    async def dispatch_message(
        self,
        message: Message
    ) -> None:
        """Dispatch message to handlers
        
        Args:
            message: Message to dispatch
        """
        message_type = message.type
        
        if message_type in self._handlers:
            for handler in self._handlers[message_type]:
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(
                        f"Handler {handler.__name__} failed: {str(e)}"
                    )
    
    def message_handler(
        self,
        message_type: str
    ) -> Callable:
        """Decorator for message handlers
        
        Args:
            message_type: Type of message to handle
            
        Returns:
            Handler decorator
        """
        def decorator(func: Callable) -> Callable:
            self.register_handler(message_type, func)
            return func
        return decorator 