"""
Task tests
"""

import pytest
from typing import List

from src.core.agentverse.agents import BaseAgent
from src.core.agentverse.task import Task, TaskConfig
from src.core.agentverse.message import Message
from src.core.agentverse.testing.mocks import MockLLM, MockAgent
from src.core.agentverse.exceptions import TaskError 