"""Test registry functionality"""

import pytest
from datetime import datetime

from src.core.agentverse.environment.registry import Registry, RegistryConfig
from src.core.agentverse.environment.decorators import component_decorator

def test_registry_registration():
    """Test basic component registration"""
    registry = Registry()
    
    @component_decorator("test")
    class TestComponent:
        name = "test_component"
        description = "Test component"
        version = "1.0.0"
    
    # Register component
    registry.register_class(TestComponent)
    
    # Verify registration
    components = registry.list_components()
    assert "test.test_component" in components
    assert components["test.test_component"]["name"] == "test_component"
    assert components["test.test_component"]["version"] == "1.0.0"

def test_registry_duplicate_registration():
    """Test duplicate registration handling"""
    registry = Registry(RegistryConfig(allow_duplicates=False))
    
    @component_decorator("test")
    class TestComponent:
        name = "test_component"
    
    # First registration should succeed
    registry.register_class(TestComponent)
    
    # Second registration should fail
    with pytest.raises(KeyError):
        registry.register_class(TestComponent)

def test_registry_usage_tracking():
    """Test component usage tracking"""
    registry = Registry(RegistryConfig(track_usage=True))
    
    @component_decorator("test")
    class TestComponent:
        name = "test_component"
    
    registry.register_class(TestComponent)
    
    # Get component multiple times
    for _ in range(3):
        registry.get("test.test_component")
    
    # Verify usage count
    components = registry.list_components()
    assert components["test.test_component"]["usage_count"] == 3

def test_registry_invalid_component():
    """Test registration of non-decorated component"""
    registry = Registry()
    
    class TestComponent:
        name = "test_component"
    
    # Should fail without decorator
    with pytest.raises(ValueError):
        registry.register_class(TestComponent) 