"""Testing Package"""

from src.core.agentverse.llm import register_llm
from src.core.agentverse.testing.mocks.llm import MockLLM

# Register mock components
register_llm("mock", MockLLM)

__all__ = [
    "MockLLM"
] 