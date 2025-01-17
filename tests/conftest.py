"""Test configuration"""

import pytest
import asyncio
from pytest_asyncio import fixture

@pytest.fixture(scope="session")
def event_loop_policy():
    """Create event loop policy"""
    return asyncio.DefaultEventLoopPolicy()

@pytest.fixture
def event_loop(event_loop_policy):
    """Create event loop with specified policy"""
    loop = event_loop_policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_tasks():
    """Sample tasks for testing"""
    return [
        {"id": 1, "action": "test1", "args": {"value": 10}},
        {"id": 2, "action": "test2", "args": {"value": 20}},
        {"id": 3, "action": "test3", "args": {"value": 30}}
    ]

@pytest.fixture
def sample_config():
    """Sample configuration for testing"""
    return {
        "name": "test",
        "version": "1.0.0",
        "description": "Test configuration",
        "metadata": {
            "created_at": datetime.utcnow().isoformat()
        }
    } 