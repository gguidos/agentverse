"""
In-memory message bus implementation for testing
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, List
from collections import defaultdict

from src.core.agentverse.message_bus.base import BaseMessageBus
from src.core.agentverse.exceptions import MessageBusError

logger = logging.getLogger(__name__)

class InMemoryMessageBus(BaseMessageBus):
    """In-memory implementation of message bus for testing"""
    
    def __init__(self):
        """Initialize in-memory message bus"""
        self.channels: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._connected = False
        logger.info("Initialized in-memory message bus")
    
    async def connect(self) -> None:
        """Connect to in-memory bus"""
        self._connected = True
        logger.debug("Connected to in-memory bus")
    
    async def disconnect(self) -> None:
        """Disconnect from in-memory bus"""
        self._connected = False
        # Clear all channels and subscribers
        self.channels.clear()
        self.subscribers.clear()
        logger.debug("Disconnected from in-memory bus")
    
    async def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """Publish message to channel
        
        Args:
            channel: Channel name
            message: Message to publish
        
        Raises:
            MessageBusError: If not connected
        """
        if not self._connected:
            raise MessageBusError("Not connected to message bus")
            
        try:
            # Store message in channel
            self.channels[channel].append(message)
            
            # Notify all subscribers
            for queue in self.subscribers[channel]:
                await queue.put(message)
                
            logger.debug(f"Published message to channel '{channel}'")
            
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise MessageBusError(f"Publish failed: {e}")
    
    async def subscribe(self, channel: str) -> None:
        """Subscribe to channel
        
        Args:
            channel: Channel to subscribe to
            
        Raises:
            MessageBusError: If not connected
        """
        if not self._connected:
            raise MessageBusError("Not connected to message bus")
            
        try:
            # Create queue for this subscription
            queue = asyncio.Queue()
            self.subscribers[channel].append(queue)
            
            logger.debug(f"Subscribed to channel '{channel}'")
            
            # Process messages from queue
            while True:
                try:
                    message = await queue.get()
                    await self._handle_message(channel, message)
                    queue.task_done()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
                    
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            raise MessageBusError(f"Subscribe failed: {e}")
    
    async def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from channel
        
        Args:
            channel: Channel to unsubscribe from
        """
        if channel in self.subscribers:
            self.subscribers[channel].clear()
            logger.debug(f"Unsubscribed from channel '{channel}'")
    
    def get_channel_messages(self, channel: str) -> List[Dict[str, Any]]:
        """Get all messages in channel (for testing)
        
        Args:
            channel: Channel name
            
        Returns:
            List of messages
        """
        return self.channels.get(channel, [])
    
    def get_subscriber_count(self, channel: str) -> int:
        """Get number of subscribers to channel (for testing)
        
        Args:
            channel: Channel name
            
        Returns:
            Number of subscribers
        """
        return len(self.subscribers.get(channel, [])) 