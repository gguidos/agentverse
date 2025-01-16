from typing import List, Dict, Any, Optional, ClassVar
import logging
from datetime import datetime

from src.core.agentverse.environment.selectors.base import (
    BaseSelector,
    SelectorConfig,
    SelectionMetrics
)
from src.core.agentverse.environment.registry import selector_registry
from src.core.agentverse.environment.base import BaseEnvironment
from src.core.agentverse.message.base import Message
from src.core.agentverse.environment.exceptions import ActionError

logger = logging.getLogger(__name__)

class BasicSelectorConfig(SelectorConfig):
    """Configuration for basic selector"""
    filter_empty: bool = True
    max_length: int = 1000
    min_length: int = 1
    remove_duplicates: bool = True
    normalize_whitespace: bool = True
    trim_messages: bool = True
    max_selections: Optional[int] = None
    
    class Config:
        extra = "allow"

@selector_registry.register("basic")
class BasicSelector(BaseSelector):
    """Basic message selector with essential filtering"""
    
    name: ClassVar[str] = "basic_selector"
    description: ClassVar[str] = "Basic message selector with essential filtering"
    version: ClassVar[str] = "1.1.0"
    
    def __init__(
        self,
        config: Optional[BasicSelectorConfig] = None
    ):
        super().__init__(config=config or BasicSelectorConfig())
        self.seen_messages: Dict[str, datetime] = {}
    
    async def _select_messages(
        self,
        environment: BaseEnvironment,
        messages: List[Message]
    ) -> List[Message]:
        """Simple message selection with basic filtering
        
        Args:
            environment: Environment instance
            messages: Pre-filtered messages
            
        Returns:
            Selected messages
            
        Raises:
            ActionError: If selection fails
        """
        try:
            selected = messages
            
            # Normalize whitespace if configured
            if self.config.normalize_whitespace:
                selected = [
                    self._normalize_message(message)
                    for message in selected
                ]
            
            # Trim messages if configured
            if self.config.trim_messages:
                selected = [
                    self._trim_message(message)
                    for message in selected
                ]
            
            # Remove duplicates if configured
            if self.config.remove_duplicates:
                selected = self._remove_duplicates(selected)
            
            # Apply max selections if configured
            if self.config.max_selections:
                selected = selected[:self.config.max_selections]
            
            return selected
            
        except Exception as e:
            logger.error(f"Basic selection failed: {str(e)}")
            raise ActionError(
                message=f"Basic selection failed: {str(e)}",
                action=self.name,
                details={
                    "messages": len(messages),
                    "config": self.config.model_dump()
                }
            )
    
    def _normalize_message(self, message: Message) -> Message:
        """Normalize message whitespace
        
        Args:
            message: Message to normalize
            
        Returns:
            Normalized message
        """
        if message.content:
            # Replace multiple spaces with single space
            content = " ".join(message.content.split())
            message.content = content
        return message
    
    def _trim_message(self, message: Message) -> Message:
        """Trim message content
        
        Args:
            message: Message to trim
            
        Returns:
            Trimmed message
        """
        if message.content:
            message.content = message.content.strip()
        return message
    
    def _remove_duplicates(self, messages: List[Message]) -> List[Message]:
        """Remove duplicate messages
        
        Args:
            messages: Messages to deduplicate
            
        Returns:
            Deduplicated messages
        """
        seen_content = set()
        unique_messages = []
        
        for message in messages:
            if message.content:
                content = message.content.strip().lower()
                if content not in seen_content:
                    seen_content.add(content)
                    unique_messages.append(message)
            else:
                unique_messages.append(message)
        
        return unique_messages
    
    def _is_duplicate(self, message: Message) -> bool:
        """Check if message is a duplicate
        
        Args:
            message: Message to check
            
        Returns:
            Whether message is duplicate
        """
        if not message.content:
            return False
            
        content = message.content.strip().lower()
        now = datetime.utcnow()
        
        # Check if content was seen recently
        if content in self.seen_messages:
            last_seen = self.seen_messages[content]
            # Consider duplicate if seen in last hour
            if (now - last_seen).total_seconds() < 3600:
                return True
        
        # Update seen messages
        self.seen_messages[content] = now
        
        # Clean up old entries
        self._cleanup_seen_messages()
        
        return False
    
    def _cleanup_seen_messages(self) -> None:
        """Clean up old seen message entries"""
        now = datetime.utcnow()
        self.seen_messages = {
            content: timestamp
            for content, timestamp in self.seen_messages.items()
            if (now - timestamp).total_seconds() < 3600
        }
    
    def reset(self) -> None:
        """Reset selector state"""
        super().reset()
        self.seen_messages.clear() 