"""
Describers Module

This module provides description and documentation generation capabilities for AgentVerse:

1. Description Types:
   - Agent Descriptions: Capabilities and behaviors
   - Memory Descriptions: Storage and retrieval patterns
   - Message Descriptions: Communication protocols
   - System Descriptions: Architecture and components

2. Description Features:
   - Natural Language Generation
   - Schema Documentation
   - API Documentation
   - Usage Examples

3. Description Formats:
   - Markdown
   - JSON Schema
   - OpenAPI
   - Natural Text

Example Usage:
    ```python
    from src.core.agentverse.describers import (
        AgentDescriber,
        MemoryDescriber,
        SchemaDescriber
    )

    # Describe an agent
    agent_desc = AgentDescriber.describe(
        agent_id="helper_agent",
        format="markdown",
        include_examples=True
    )

    # Generate memory schema
    memory_schema = MemoryDescriber.generate_schema(
        memory_type="vector",
        backend="faiss"
    )

    # Document API
    api_docs = SchemaDescriber.generate_openapi(
        title="AgentVerse API",
        version="1.0.0",
        components=["agents", "memory", "messages"]
    )
    ```

Description Structure:
    ```
    Description
    ├── Overview
    │   ├── Purpose
    │   ├── Features
    │   └── Architecture
    ├── Components
    │   ├── Interfaces
    │   ├── Models
    │   └── Examples
    ├── Usage
    │   ├── Setup
    │   ├── Configuration
    │   └── Examples
    └── References
        ├── API Docs
        ├── Schemas
        └── Links
    ```
"""

from src.core.agentverse.environment.describers.base import BaseDescriber
from src.core.agentverse.environment.describers.agent import AgentDescriber
from src.core.agentverse.environment.describers.memory import MemoryDescriber
from src.core.agentverse.environment.describers.schema import SchemaDescriber
from src.core.agentverse.environment.describers.markdown import MarkdownDescriber

__all__ = [
    'BaseDescriber',
    'AgentDescriber',
    'MemoryDescriber',
    'SchemaDescriber',
    'MarkdownDescriber'
]

# Version
__version__ = "1.0.0" 