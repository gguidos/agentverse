"""Memory Service Module"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MemoryService:
    """Service for managing agent memory"""
    
    def __init__(self):
        self.contexts = {}  # Store contexts in memory
        logger.info("Initialized memory service")
        
    async def initialize(self):
        """Initialize memory service"""
        logger.info("Memory service initialized")
        
    async def get_context(self, session_id: str = None) -> Dict[str, Any]:
        """Get context for a session"""
        return self.contexts.get(session_id, {})
        
    async def save_context(self, context: Dict[str, Any], session_id: str = None):
        """Save context for a session"""
        self.contexts[session_id] = context
        
    async def clear_context(self, session_id: str = None):
        """Clear context for a session"""
        if session_id in self.contexts:
            del self.contexts[session_id] 