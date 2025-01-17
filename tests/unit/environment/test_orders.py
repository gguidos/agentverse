"""Test order implementations"""

import pytest
from datetime import datetime

from src.core.agentverse.environment.orders.base import OrderStatus, OrderResult
from src.core.agentverse.environment.orders.sequential import SequentialOrder
from src.core.agentverse.environment.orders.parallel import ParallelOrder
from src.core.agentverse.environment.orders.conditional import ConditionalOrder
from src.core.agentverse.environment.orders.random import RandomOrder

@pytest.mark.asyncio
async def test_sequential_order():
    """Test sequential order execution"""
    # Setup
    tasks = [
        {"id": 1, "action": "test1"},
        {"id": 2, "action": "test2"},
        {"id": 3, "action": "test3"}
    ]
    
    order = SequentialOrder()
    
    # Execute
    result = await order.execute(tasks=tasks)
    
    # Verify
    assert result.status == OrderStatus.COMPLETED
    assert len(result.data["results"]) == 3
    assert all(r["status"] == "completed" for r in result.data["results"])

@pytest.mark.asyncio
async def test_parallel_order():
    """Test parallel order execution"""
    # Setup
    tasks = [
        {"id": 1, "action": "test1"},
        {"id": 2, "action": "test2"},
        {"id": 3, "action": "test3"}
    ]
    
    order = ParallelOrder()
    
    # Execute
    result = await order.execute(tasks=tasks)
    
    # Verify
    assert result.status == OrderStatus.COMPLETED
    assert len(result.data["results"]) == 3
    assert result.data["completed"] == 3
    assert result.data["failed"] == 0

@pytest.mark.asyncio
async def test_conditional_order():
    """Test conditional order execution"""
    # Setup
    def condition(**kwargs):
        return kwargs.get("value", 0) > 5
    
    if_true = SequentialOrder()
    if_false = ParallelOrder()
    
    order = ConditionalOrder(
        condition=condition,
        if_true=if_true,
        if_false=if_false
    )
    
    # Test true condition
    result = await order.execute(value=10)
    assert result.data["condition_result"] is True
    assert result.data["executed_branch"] == "if_true"
    
    # Test false condition
    result = await order.execute(value=3)
    assert result.data["condition_result"] is False
    assert result.data["executed_branch"] == "if_false"

@pytest.mark.asyncio
async def test_random_order():
    """Test random order execution"""
    # Setup
    tasks = [
        {"id": 1, "action": "test1"},
        {"id": 2, "action": "test2"},
        {"id": 3, "action": "test3"}
    ]
    
    order = RandomOrder()
    
    # Execute
    result = await order.execute(tasks=tasks)
    
    # Verify
    assert result.status == OrderStatus.COMPLETED
    assert len(result.data["results"]) == 3
    assert len(result.data["execution_order"]) == 3
    # Order should be different from input order
    assert result.data["execution_order"] != list(range(len(tasks))) 