"""
Recovery mechanism tests
"""

import pytest
from src.core.agentverse.recovery import RetryHandler, circuit_breaker

@pytest.mark.asyncio
async def test_retry_handler():
    """Test retry handler"""
    retry = RetryHandler()
    retry.max_attempts = 3
    
    attempts = 0
    @retry.handle
    async def failing_function():
        nonlocal attempts
        attempts += 1
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        await failing_function()
    
    assert attempts == 3

@pytest.mark.asyncio
async def test_circuit_breaker():
    """Test circuit breaker"""
    
    failures = 0
    
    @circuit_breaker(max_failures=3)
    async def failing_function():
        nonlocal failures
        failures += 1
        raise ValueError("Test error")
    
    # Should fail 3 times then open circuit
    for i in range(5):
        try:
            await failing_function()
        except ValueError:
            # Expected for first 3 calls
            if i < 3:
                continue
        except RuntimeError as e:
            # Expected for calls after circuit opens
            assert str(e) == "Circuit breaker open"
            continue
    
    assert failures == 3  # Should stop after circuit opens 