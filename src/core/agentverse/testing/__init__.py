"""
AgentVerse Testing Infrastructure

This module provides testing utilities and fixtures for AgentVerse components.
It includes mock objects, test helpers, and common test configurations.

Key Components:
    - MockServices: Mock implementations of external services
    - TestFixtures: Common test fixtures and configurations
    - Assertions: Custom test assertions for AgentVerse
    - TestUtils: Helper functions for testing

Example Usage:
    >>> from src.core.agentverse.testing import (
    ...     MockLLMService,
    ...     AgentTestCase,
    ...     assert_agent_behavior
    ... )
    >>> 
    >>> class TestMyAgent(AgentTestCase):
    ...     async def test_agent_response(self):
    ...         agent = await self.create_test_agent()
    ...         response = await agent.process_message("Hello")
    ...         self.assert_agent_response(response, contains="Hello")
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Type, Union
from unittest.mock import MagicMock
from datetime import datetime
from pydantic import BaseModel
from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.core.agentverse.agents.base_agent import BaseAgent
from src.core.agentverse.services.llm.base import BaseLLMService
from src.core.agentverse.memory.base import BaseMemory

logger = logging.getLogger(__name__)

class MockResponse(BaseModel):
    """Mock response for testing"""
    content: str
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.utcnow()

class MockLLMService(BaseLLMService):
    """Mock LLM service for testing"""
    
    def __init__(self, responses: Optional[Dict[str, str]] = None):
        self.responses = responses or {}
        self.calls: List[Dict[str, Any]] = []
    
    async def generate(self, prompt: str, **kwargs) -> MockResponse:
        """Mock generate method"""
        self.calls.append({
            "prompt": prompt,
            "kwargs": kwargs,
            "timestamp": datetime.utcnow()
        })
        return MockResponse(
            content=self.responses.get(prompt, "Mock response")
        )
    
    def get_call_count(self) -> int:
        """Get number of calls made"""
        return len(self.calls)

class MockMemory(BaseMemory):
    """Mock memory for testing"""
    
    def __init__(self):
        self.storage: Dict[str, Any] = {}
        self.calls: List[Dict[str, Any]] = []
    
    async def store(self, key: str, value: Any) -> None:
        """Mock store method"""
        self.storage[key] = value
        self.calls.append({
            "action": "store",
            "key": key,
            "value": value
        })
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Mock retrieve method"""
        self.calls.append({
            "action": "retrieve",
            "key": key
        })
        return self.storage.get(key)

class MockRedis:
    """Mock Redis client for testing"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.calls: List[Dict[str, Any]] = []
        self._connected = False
        self.pubsub = MockPubSub()
    
    async def ping(self) -> bool:
        """Mock ping method"""
        if not self._connected:
            raise RedisError("Not connected")
        return True
    
    async def connect(self) -> None:
        """Mock connect method"""
        self._connected = True
        self.calls.append({
            "action": "connect",
            "timestamp": datetime.utcnow()
        })
    
    async def close(self) -> None:
        """Mock close method"""
        self._connected = False
        self.calls.append({
            "action": "close",
            "timestamp": datetime.utcnow()
        })
    
    async def set(
        self,
        key: str,
        value: Union[str, bytes],
        ex: Optional[int] = None
    ) -> None:
        """Mock set method"""
        self.data[key] = value
        self.calls.append({
            "action": "set",
            "key": key,
            "value": value,
            "ex": ex,
            "timestamp": datetime.utcnow()
        })
    
    async def get(self, key: str) -> Optional[Union[str, bytes]]:
        """Mock get method"""
        self.calls.append({
            "action": "get",
            "key": key,
            "timestamp": datetime.utcnow()
        })
        return self.data.get(key)
    
    async def delete(self, key: str) -> None:
        """Mock delete method"""
        if key in self.data:
            del self.data[key]
        self.calls.append({
            "action": "delete",
            "key": key,
            "timestamp": datetime.utcnow()
        })
    
    def get_call_count(self, action: Optional[str] = None) -> int:
        """Get number of calls made
        
        Args:
            action: Optional specific action to count
            
        Returns:
            Number of matching calls
        """
        if action:
            return len([c for c in self.calls if c["action"] == action])
        return len(self.calls)

class MockPubSub:
    """Mock Redis PubSub"""
    
    def __init__(self):
        self.channels: Dict[str, List[Dict[str, Any]]] = {}
        self.subscribed: List[str] = []
    
    async def subscribe(self, *channels: str) -> None:
        """Subscribe to channels"""
        for channel in channels:
            if channel not in self.subscribed:
                self.subscribed.append(channel)
                self.channels[channel] = []
    
    async def unsubscribe(self, *channels: str) -> None:
        """Unsubscribe from channels"""
        for channel in channels:
            if channel in self.subscribed:
                self.subscribed.remove(channel)
                self.channels.pop(channel, None)
    
    async def listen(self):
        """Listen for messages"""
        while True:
            for channel in self.subscribed:
                messages = self.channels.get(channel, [])
                for message in messages:
                    yield {
                        "type": "message",
                        "channel": channel,
                        "data": message
                    }
            await asyncio.sleep(0.1)

class TestConfig(BaseModel):
    """Test configuration"""
    mock_responses: Dict[str, str] = {}
    mock_memory: bool = True
    mock_services: bool = True
    async_mode: bool = True

class AgentTestCase:
    """Base test case for agent testing"""
    
    def setUp(self):
        """Set up test case"""
        self.config = TestConfig()
        self.llm = MockLLMService(responses=self.config.mock_responses)
        self.memory = MockMemory() if self.config.mock_memory else None
        self.redis = MockRedis() if self.config.mock_services else None
    
    async def create_test_agent(
        self,
        agent_class: Type[BaseAgent],
        **kwargs
    ) -> BaseAgent:
        """Create agent for testing
        
        Args:
            agent_class: Agent class to create
            **kwargs: Additional agent arguments
            
        Returns:
            Configured test agent
        """
        return agent_class(
            llm_service=self.llm,
            memory=self.memory,
            **kwargs
        )
    
    def assert_agent_response(
        self,
        response: Any,
        *,
        equals: Optional[str] = None,
        contains: Optional[str] = None,
        matches: Optional[str] = None
    ):
        """Assert agent response
        
        Args:
            response: Agent response to check
            equals: Expected exact response
            contains: Expected substring
            matches: Expected regex pattern
        """
        if equals is not None:
            assert response == equals
        if contains is not None:
            assert contains in str(response)
        if matches is not None:
            import re
            assert re.search(matches, str(response))
    
    def assert_llm_called(self, times: Optional[int] = None):
        """Assert LLM service was called
        
        Args:
            times: Expected number of calls
        """
        if times is not None:
            assert self.llm.get_call_count() == times
        else:
            assert self.llm.get_call_count() > 0
    
    def assert_memory_operation(
        self,
        operation: str,
        key: Optional[str] = None,
        value: Optional[Any] = None
    ):
        """Assert memory operation
        
        Args:
            operation: Expected operation type
            key: Expected key
            value: Expected value
        """
        if not self.memory:
            return
            
        matching_calls = [
            call for call in self.memory.calls
            if call["action"] == operation
        ]
        
        assert matching_calls, f"No {operation} operations found"
        
        if key is not None:
            assert any(
                call["key"] == key
                for call in matching_calls
            )
        
        if value is not None:
            assert any(
                call.get("value") == value
                for call in matching_calls
            )
    
    def assert_redis_operation(
        self,
        operation: str,
        key: Optional[str] = None,
        value: Optional[Any] = None,
        times: Optional[int] = None
    ):
        """Assert Redis operation
        
        Args:
            operation: Expected operation type
            key: Expected key
            value: Expected value
            times: Expected number of calls
        """
        if not self.redis:
            return
            
        matching_calls = [
            call for call in self.redis.calls
            if call["action"] == operation
        ]
        
        if times is not None:
            assert len(matching_calls) == times, \
                f"Expected {times} {operation} calls, got {len(matching_calls)}"
        else:
            assert matching_calls, f"No {operation} operations found"
        
        if key is not None:
            assert any(
                call.get("key") == key
                for call in matching_calls
            )
        
        if value is not None:
            assert any(
                call.get("value") == value
                for call in matching_calls
            )

def async_test(f):
    """Decorator for async tests"""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))
    return wrapper

__all__ = [
    "MockLLMService",
    "MockMemory",
    "MockRedis",
    "MockResponse",
    "AgentTestCase",
    "TestConfig",
    "async_test"
] 