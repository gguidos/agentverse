import pytest
from src.core.agentverse.recovery import RetryHandler
from src.core.infrastructure.circuit_breaker import circuit_breaker

@pytest.mark.asyncio
async def test_retry_handler():
    retry = RetryHandler(max_retries=3)
    call_count = 0
    
    @retry.wrap
    async def failing_function():
        nonlocal call_count
        call_count += 1
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        await failing_function()
    
    assert call_count == 3  # Should retry 3 times

@pytest.mark.asyncio
async def test_circuit_breaker():
    @circuit_breaker
    async def failing_function():
        raise ValueError("Test error")
    
    # Should open circuit after multiple failures
    for _ in range(5):
        try:
            await failing_function()
        except ValueError:
            pass 