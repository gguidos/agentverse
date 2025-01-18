from typing import List, Dict, Any, ClassVar, Optional
import logging
from datetime import datetime, timedelta

from src.core.agentverse.tools.base import BaseTool, ToolResult, ToolConfig, ToolExecutionError
from src.core.agentverse.memory.base import Message
from src.core.agentverse.memory.agent_memory import AgentMemoryStore
from src.core.agentverse.llm.base import BaseLLM
from src.core.agentverse.tools.registry import tool_registry
from src.core.agentverse.tools.types import AgentCapability, ToolType

logger = logging.getLogger(__name__)

class MemoryToolConfig(ToolConfig):
    """Memory tool specific configuration"""
    max_results: int = 10
    min_similarity: float = 0.7
    context_window: int = 5  # Number of messages before/after match
    max_context_length: int = 2000
    enable_summarization: bool = True

@tool_registry.register(AgentCapability.MEMORY, ToolType.COMPLEX)
class MemoryTool(BaseTool):
    """Tool for searching and analyzing agent memory"""
    
    name: ClassVar[str] = "memory"
    description: ClassVar[str] = """
    Search and analyze conversation history and agent memory.
    Supports semantic search, context retrieval, and memory summarization.
    """
    version: ClassVar[str] = "1.1.0"
    capabilities: ClassVar[List[str]] = [AgentCapability.MEMORY]
    required_dependencies = {
        "memory_store": "MemoryStore",
        "llm": "BaseLLM"
    }
    parameters: ClassVar[Dict[str, Any]] = {
        "operation": {
            "type": "string",
            "description": "The memory operation to perform",
            "required": True,
            "enum": ["search", "context", "summarize", "recent"]
        },
        "query": {
            "type": "string",
            "description": "Search query or topic",
            "required": True
        },
        "agent_id": {
            "type": "string",
            "description": "ID of agent whose memory to search",
            "required": True
        },
        "limit": {
            "type": "integer",
            "description": "Maximum number of results",
            "minimum": 1,
            "maximum": 10,
            "default": 5
        },
        "time_window": {
            "type": "string",
            "description": "Time window for search (e.g., '1h', '1d', '7d')",
            "pattern": r"^\d+[hdw]$",
            "default": "1d"
        }
    }
    required_permissions: ClassVar[List[str]] = ["memory_access"]
    
    def __init__(
        self,
        memory_store: AgentMemoryStore,
        llm: BaseLLM,
        config: Optional[MemoryToolConfig] = None
    ):
        super().__init__(config=config or MemoryToolConfig())
        self.memory_store = memory_store
        self.llm = llm
    
    def _parse_time_window(self, window: str) -> timedelta:
        """Parse time window string into timedelta"""
        try:
            value = int(window[:-1])
            unit = window[-1]
            if unit == 'h':
                return timedelta(hours=value)
            elif unit == 'd':
                return timedelta(days=value)
            elif unit == 'w':
                return timedelta(weeks=value)
            else:
                raise ValueError(f"Invalid time unit: {unit}")
        except Exception as e:
            logger.error(f"Time window parsing error: {str(e)}")
            return timedelta(days=1)  # Default to 1 day
    
    async def execute(
        self,
        operation: str,
        query: str,
        agent_id: str,
        limit: int = 5,
        time_window: str = "1d"
    ) -> ToolResult:
        """Execute memory operations"""
        try:
            if operation == "search":
                return await self._search_memory(query, agent_id, limit, time_window)
            elif operation == "context":
                return await self._get_context(query, agent_id, limit)
            elif operation == "summarize":
                return await self._summarize_memory(query, agent_id, time_window)
            elif operation == "recent":
                return await self._get_recent(agent_id, limit)
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.error(f"Memory operation error: {str(e)}")
            raise ToolExecutionError(f"Memory operation failed: {str(e)}", e)
    
    async def _search_memory(
        self,
        query: str,
        agent_id: str,
        limit: int,
        time_window: str
    ) -> ToolResult:
        """Search through agent's memory"""
        try:
            # Calculate time range
            window = self._parse_time_window(time_window)
            start_time = datetime.utcnow() - window
            
            # Get messages from memory store
            messages = await self.memory_store.get_messages(
                agent_id=agent_id,
                start_time=start_time,
                limit=limit,
                query=query,
                min_similarity=self.config.min_similarity
            )
            
            if not messages:
                return ToolResult(
                    success=True,
                    result=[],
                    metadata={
                        "query": query,
                        "time_window": time_window,
                        "count": 0
                    }
                )
            
            return ToolResult(
                success=True,
                result=[{
                    "content": msg.content,
                    "sender": msg.sender,
                    "timestamp": msg.timestamp.isoformat(),
                    "type": msg.type,
                    "metadata": msg.metadata
                } for msg in messages],
                metadata={
                    "query": query,
                    "time_window": time_window,
                    "count": len(messages)
                }
            )
            
        except Exception as e:
            logger.error(f"Memory search error: {str(e)}")
            raise ToolExecutionError(f"Memory search failed: {str(e)}", e)
    
    async def _get_context(
        self,
        message_id: str,
        agent_id: str,
        context_size: int
    ) -> ToolResult:
        """Get conversation context around a message"""
        try:
            # Get the target message and surrounding context
            context = await self.memory_store.get_message_context(
                agent_id=agent_id,
                message_id=message_id,
                context_size=context_size
            )
            
            if not context:
                return ToolResult(
                    success=False,
                    error=f"Message {message_id} not found"
                )
            
            return ToolResult(
                success=True,
                result={
                    "target_message": {
                        "content": context.target.content,
                        "sender": context.target.sender,
                        "timestamp": context.target.timestamp.isoformat()
                    },
                    "before": [{
                        "content": msg.content,
                        "sender": msg.sender,
                        "timestamp": msg.timestamp.isoformat()
                    } for msg in context.before],
                    "after": [{
                        "content": msg.content,
                        "sender": msg.sender,
                        "timestamp": msg.timestamp.isoformat()
                    } for msg in context.after]
                },
                metadata={
                    "message_id": message_id,
                    "context_size": context_size
                }
            )
            
        except Exception as e:
            logger.error(f"Context retrieval error: {str(e)}")
            raise ToolExecutionError(f"Context retrieval failed: {str(e)}", e)
    
    async def _summarize_memory(
        self,
        topic: str,
        agent_id: str,
        time_window: str
    ) -> ToolResult:
        """Summarize memory content about a topic"""
        try:
            if not self.config.enable_summarization:
                return ToolResult(
                    success=False,
                    error="Memory summarization is disabled"
                )
            
            # Get relevant messages
            messages = await self._search_memory(
                query=topic,
                agent_id=agent_id,
                limit=self.config.max_results,
                time_window=time_window
            )
            
            if not messages.success or not messages.result:
                return ToolResult(
                    success=False,
                    error="No relevant messages found for summarization"
                )
            
            # Prepare content for summarization
            content = "\n\n".join(
                f"{msg['sender']}: {msg['content']}"
                for msg in messages.result
            )
            
            if len(content) > self.config.max_context_length:
                content = content[:self.config.max_context_length] + "..."
            
            # Generate summary
            prompt = f"""Please provide a concise summary of the following conversation about {topic}:

{content}

Summary:"""
            
            response = await self.llm.generate_response(prompt=prompt)
            
            return ToolResult(
                success=True,
                result={
                    "summary": response.content,
                    "topic": topic,
                    "message_count": len(messages.result),
                    "time_window": time_window
                }
            )
            
        except Exception as e:
            logger.error(f"Memory summarization error: {str(e)}")
            raise ToolExecutionError(f"Memory summarization failed: {str(e)}", e)
    
    async def _get_recent(
        self,
        agent_id: str,
        limit: int
    ) -> ToolResult:
        """Get most recent messages"""
        try:
            messages = await self.memory_store.get_messages(
                agent_id=agent_id,
                limit=limit,
                sort="timestamp",
                order="desc"
            )
            
            return ToolResult(
                success=True,
                result=[{
                    "content": msg.content,
                    "sender": msg.sender,
                    "timestamp": msg.timestamp.isoformat(),
                    "type": msg.type
                } for msg in messages],
                metadata={
                    "count": len(messages),
                    "agent_id": agent_id
                }
            )
            
        except Exception as e:
            logger.error(f"Recent messages retrieval error: {str(e)}")
            raise ToolExecutionError(f"Recent messages retrieval failed: {str(e)}", e) 