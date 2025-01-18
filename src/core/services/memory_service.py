"""Memory Service Module"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MemoryService:
    """Service for managing agent memory"""
    
    def __init__(self, memory_store=None):
        """Initialize memory service
        
        Args:
            memory_store: Optional memory store implementation
        """
        self.memory_store = memory_store
        logger.info("Initialized memory service")
    
    async def initialize(self):
        """Initialize memory service resources"""
        try:
            if self.memory_store:
                await self.memory_store.initialize()
            logger.info("Memory service initialized")
        except Exception as e:
            logger.error(f"Error initializing memory service: {str(e)}")
            raise

    async def get_context(self) -> Dict[str, Any]:
        """Get current context from memory"""
        try:
            if self.memory_store:
                return await self.memory_store.get_context()
            return {}
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            return {}

    async def add_interaction(self, message: str, response: str):
        """Add interaction to memory"""
        try:
            if self.memory_store:
                await self.memory_store.add_interaction(message, response)
        except Exception as e:
            logger.error(f"Error adding interaction: {str(e)}")
            raise

    async def create_memory(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """Create memory instance for an agent
        
        Args:
            agent_id: Agent identifier
            config: Optional memory configuration
            
        Returns:
            Memory instance
        """
        try:
            if self.memory_store:
                return await self.memory_store.create_memory(agent_id, config)
            return None
        except Exception as e:
            logger.error(f"Error creating memory: {str(e)}")
            raise 