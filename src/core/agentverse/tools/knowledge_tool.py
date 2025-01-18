from typing import Dict, Any, ClassVar, List, Optional
import logging
import numpy as np
import json
import base64
from io import BytesIO
from datetime import timedelta
import hashlib
import pickle
from redis import Redis

from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.manifold import TSNE
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.core.agentverse.tools.base import BaseTool, ToolResult, ToolConfig, ToolExecutionError
from src.core.agentverse.llm.base import BaseLLM
from src.core.agentverse.memory.vectorstore import VectorstoreMemoryService
from src.core.agentverse.tools.registry import tool_registry
from src.core.agentverse.tools.types import AgentCapability, ToolType

logger = logging.getLogger(__name__)

class KnowledgeToolConfig(ToolConfig):
    """Knowledge tool specific configuration"""
    cache_ttl: int = 3600  # 1 hour
    min_confidence: float = 0.5
    max_context_length: int = 2000
    enable_visualization: bool = True
    max_results: int = 50
    clustering_min_docs: int = 5

@tool_registry.register(AgentCapability.KNOWLEDGE, ToolType.COMPLEX)
class KnowledgeTool(BaseTool):
    """Tool for searching and analyzing knowledge base"""
    
    name: ClassVar[str] = "knowledge"
    description: ClassVar[str] = """
    Search and analyze knowledge base using semantic search and LLM processing.
    Supports search, QA, summarization, topic extraction, and visualization.
    """
    version: ClassVar[str] = "1.1.0"
    capabilities: ClassVar[List[str]] = [AgentCapability.KNOWLEDGE]
    required_dependencies = {
        "vectorstore": "VectorstoreMemoryService",
        "llm": "BaseLLM",
        "redis_client": "Redis"
    }
    
    parameters: ClassVar[Dict[str, Any]] = {
        "operation": {
            "type": "string",
            "description": "The operation to perform",
            "required": True,
            "enum": ["search", "qa", "summarize", "topics", "cluster", "visualize"]
        },
        "query": {
            "type": "string",
            "description": "Search query or question",
            "required": True
        },
        "collection": {
            "type": "string",
            "description": "Knowledge base collection to search",
            "required": True
        },
        "limit": {
            "type": "integer",
            "description": "Maximum number of results",
            "minimum": 1,
            "maximum": 50,
            "default": 5
        },
        "min_score": {
            "type": "number",
            "description": "Minimum similarity score (0-1)",
            "minimum": 0,
            "maximum": 1,
            "default": 0.5
        },
        "num_clusters": {
            "type": "integer",
            "description": "Number of clusters for clustering",
            "minimum": 2,
            "maximum": 10,
            "default": 3
        },
        "visualization_type": {
            "type": "string",
            "description": "Type of visualization",
            "enum": ["cluster_map", "similarity_matrix", "topic_distribution"],
            "default": "cluster_map"
        }
    }
    
    def __init__(
        self,
        vectorstore: VectorstoreMemoryService,
        llm: BaseLLM,
        redis_client: Redis,
        config: Optional[KnowledgeToolConfig] = None
    ):
        super().__init__(config=config or KnowledgeToolConfig())
        self.vectorstore = vectorstore
        self.llm = llm
        self.redis = redis_client
        
    def _get_cache_key(self, operation: str, **kwargs) -> str:
        """Generate cache key for operation"""
        key_parts = [operation] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
        return f"knowledge_tool:{hashlib.md5(':'.join(key_parts).encode()).hexdigest()}"
    
    async def _get_cached_result(self, key: str) -> Optional[ToolResult]:
        """Get cached result if available"""
        try:
            cached = await self.redis.get(key)
            if cached:
                return pickle.loads(cached)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {str(e)}")
        return None
    
    async def _cache_result(self, key: str, result: ToolResult) -> None:
        """Cache operation result"""
        try:
            await self.redis.setex(
                key,
                timedelta(seconds=self.config.cache_ttl),
                pickle.dumps(result)
            )
        except Exception as e:
            logger.warning(f"Cache storage failed: {str(e)}")
    
    async def execute(
        self,
        operation: str,
        query: str,
        collection: str,
        limit: int = 5,
        min_score: float = 0.5,
        num_clusters: int = 3,
        visualization_type: str = "cluster_map"
    ) -> ToolResult:
        """Execute knowledge operations"""
        try:
            # Check cache first
            cache_key = self._get_cache_key(
                operation,
                query=query,
                collection=collection,
                limit=limit,
                min_score=min_score,
                num_clusters=num_clusters,
                visualization_type=visualization_type
            )
            
            cached_result = await self._get_cached_result(cache_key)
            if cached_result:
                return cached_result
            
            # Execute operation
            if operation == "search":
                result = await self._search(query, collection, limit, min_score)
            elif operation == "qa":
                result = await self._question_answer(query, collection, limit, min_score)
            elif operation == "summarize":
                result = await self._summarize(query, collection, limit, min_score)
            elif operation == "topics":
                result = await self._extract_topics(query, collection, limit, min_score)
            elif operation == "cluster":
                result = await self._cluster_documents(query, collection, limit, num_clusters)
            elif operation == "visualize":
                result = await self._visualize_documents(
                    query, collection, limit, min_score,
                    num_clusters, visualization_type
                )
            else:
                raise ValueError(f"Unknown operation: {operation}")
            
            # Cache successful result
            if result.success:
                await self._cache_result(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Knowledge operation error: {str(e)}")
            raise ToolExecutionError(f"Knowledge operation failed: {str(e)}", e)
    
    async def _search(
        self,
        query: str,
        collection: str,
        limit: int,
        min_score: float
    ) -> ToolResult:
        """Search knowledge base"""
        results = await self.vectorstore.search(
            collection=collection,
            query=query,
            limit=limit,
            min_score=min_score
        )
        
        return ToolResult(
            success=True,
            result=[{
                "content": r.content,
                "score": r.score,
                "metadata": r.metadata
            } for r in results],
            metadata={
                "query": query,
                "count": len(results)
            }
        )
    
    async def _question_answer(
        self,
        question: str,
        collection: str,
        limit: int,
        min_score: float
    ) -> ToolResult:
        """Answer questions using knowledge base"""
        # Get relevant documents
        results = await self.vectorstore.search(
            collection=collection,
            query=question,
            limit=limit,
            min_score=min_score
        )
        
        if not results:
            return ToolResult(
                success=False,
                error="No relevant documents found"
            )
        
        # Prepare context
        context = "\n\n".join(r.content for r in results)
        if len(context) > self.config.max_context_length:
            context = context[:self.config.max_context_length] + "..."
        
        # Generate answer
        prompt = f"""Based on the following context, answer the question. If the answer cannot be found in the context, say so.

Context:
{context}

Question: {question}

Answer:"""
        
        response = await self.llm.generate_response(prompt=prompt)
        
        return ToolResult(
            success=True,
            result={
                "answer": response.content,
                "sources": [{
                    "content": r.content[:200] + "...",
                    "score": r.score,
                    "metadata": r.metadata
                } for r in results]
            },
            metadata={
                "question": question,
                "context_length": len(context)
            }
        )
    
    # ... Additional methods (_summarize, _extract_topics, _cluster_documents, _visualize_documents)
    # would follow similar patterns with proper error handling, caching, and metadata 