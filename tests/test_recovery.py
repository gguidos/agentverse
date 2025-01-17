"""Recovery mechanism tests"""

import pytest
import logging
from src.core.agentverse.recovery import RetryHandler, CircuitBreaker, circuit_breaker

@pytest.mark.asyncio
async def test_retry_handler(caplog):
    """Test retry handler"""
    handler = RetryHandler(max_retries=3)
    
    async def failing_operation():
        raise ValueError("Test error")
    
    with caplog.at_level(logging.WARNING):
        with pytest.raises(ValueError):
            await handler.handle(failing_operation)
    
    # Verify retry attempts were logged
    assert len([r for r in caplog.records if "Attempt" in r.message]) == 3

@pytest.mark.asyncio
async def test_circuit_breaker(caplog):
    """Test circuit breaker"""
    breaker = CircuitBreaker(failure_threshold=2)
    
    async def failing_operation():
        raise ValueError("Test error")
    
    with caplog.at_level(logging.ERROR):
        # Trigger circuit breaker
        for _ in range(3):
            with pytest.raises((ValueError, RuntimeError)):
                await breaker.execute(failing_operation)
    
    # Verify circuit open messages were logged
    assert len([r for r in caplog.records if "Circuit open" in r.message]) == 1 