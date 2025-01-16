from typing import Dict, Any, ClassVar, Optional, List
import logging
import numpy as np
from datetime import datetime

from src.core.agentverse.tools.base import BaseTool, ToolResult, ToolConfig, ToolExecutionError
from src.core.agentverse.memory.vectorstore import VectorstoreService
from src.core.agentverse.llm.base import BaseLLM

logger = logging.getLogger(__name__)

class SearchToolConfig(ToolConfig):
    """Search tool specific configuration"""
    max_results: int = 10
    min_similarity: float = 0.7
    rerank_results: bool = True
    combine_similar: bool = True
    max_context_length: int = 2000
    enable_hybrid_search: bool = True
    hybrid_search_weights: Dict[str, float] = {
        "semantic": 0.7,
        "keyword": 0.3
    }

class SearchTool(BaseTool):
    """Tool for semantic and hybrid search across knowledge bases"""
    
    name: ClassVar[str] = "search"
    description: ClassVar[str] = """
    Search through knowledge bases using semantic similarity and hybrid search.
    Supports multiple collections, result reranking, and context combination.
    """
    version: ClassVar[str] = "1.1.0"
    parameters: ClassVar[Dict[str, Any]] = {
        "query": {
            "type": "string",
            "description": "Search query",
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
            "maximum": 20,
            "default": 5
        },
        "min_score": {
            "type": "number",
            "description": "Minimum similarity score (0-1)",
            "minimum": 0,
            "maximum": 1,
            "default": 0.7
        },
        "search_type": {
            "type": "string",
            "description": "Type of search to perform",
            "enum": ["semantic", "keyword", "hybrid"],
            "default": "hybrid"
        },
        "filters": {
            "type": "object",
            "description": "Optional filters for search",
            "required": False
        }
    }
    required_permissions: ClassVar[List[str]] = ["search_access"]
    
    def __init__(
        self,
        vectorstore: VectorstoreService,
        llm: Optional[BaseLLM] = None,
        config: Optional[SearchToolConfig] = None
    ):
        super().__init__(config=config or SearchToolConfig())
        self.vectorstore = vectorstore
        self.llm = llm
    
    async def execute(
        self,
        query: str,
        collection: str,
        limit: int = 5,
        min_score: float = 0.7,
        search_type: str = "hybrid",
        filters: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Execute search operation"""
        try:
            if search_type == "hybrid" and self.config.enable_hybrid_search:
                return await self._hybrid_search(
                    query, collection, limit, min_score, filters
                )
            elif search_type == "keyword":
                return await self._keyword_search(
                    query, collection, limit, filters
                )
            else:
                return await self._semantic_search(
                    query, collection, limit, min_score, filters
                )
                
        except Exception as e:
            logger.error(f"Search operation error: {str(e)}")
            raise ToolExecutionError(f"Search operation failed: {str(e)}", e)
    
    async def _semantic_search(
        self,
        query: str,
        collection: str,
        limit: int,
        min_score: float,
        filters: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Perform semantic search"""
        results = await self.vectorstore.search(
            collection=collection,
            query=query,
            limit=limit,
            min_score=min_score,
            filters=filters
        )
        
        if not results:
            return ToolResult(
                success=True,
                result=[],
                metadata={
                    "query": query,
                    "collection": collection,
                    "search_type": "semantic",
                    "count": 0
                }
            )
        
        # Rerank if enabled
        if self.config.rerank_results and self.llm:
            results = await self._rerank_results(query, results)
        
        # Combine similar results if enabled
        if self.config.combine_similar:
            results = self._combine_similar_results(results)
        
        return ToolResult(
            success=True,
            result=[{
                "content": r.content,
                "score": r.score,
                "metadata": r.metadata,
                "source": r.metadata.get("source", "unknown")
            } for r in results],
            metadata={
                "query": query,
                "collection": collection,
                "search_type": "semantic",
                "count": len(results)
            }
        )
    
    async def _keyword_search(
        self,
        query: str,
        collection: str,
        limit: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Perform keyword-based search"""
        results = await self.vectorstore.keyword_search(
            collection=collection,
            query=query,
            limit=limit,
            filters=filters
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
                "collection": collection,
                "search_type": "keyword",
                "count": len(results)
            }
        )
    
    async def _hybrid_search(
        self,
        query: str,
        collection: str,
        limit: int,
        min_score: float,
        filters: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Perform hybrid search combining semantic and keyword results"""
        # Get results from both methods
        semantic_results = await self._semantic_search(
            query, collection, limit * 2, min_score, filters
        )
        keyword_results = await self._keyword_search(
            query, collection, limit * 2, filters
        )
        
        # Combine and score results
        combined_results = self._combine_hybrid_results(
            semantic_results.result,
            keyword_results.result,
            self.config.hybrid_search_weights
        )
        
        # Take top results
        final_results = combined_results[:limit]
        
        return ToolResult(
            success=True,
            result=final_results,
            metadata={
                "query": query,
                "collection": collection,
                "search_type": "hybrid",
                "count": len(final_results),
                "weights": self.config.hybrid_search_weights
            }
        )
    
    async def _rerank_results(self, query: str, results: List[Any]) -> List[Any]:
        """Rerank results using LLM"""
        if not self.llm:
            return results
            
        try:
            # Create reranking prompt
            prompt = f"""Rate how relevant each result is to the query on a scale of 0-10.
            
Query: {query}

Results:
{self._format_results_for_reranking(results)}

Ratings (format as JSON array of numbers):"""
            
            response = await self.llm.generate_response(prompt=prompt)
            ratings = self._parse_ratings(response.content)
            
            # Combine original scores with LLM ratings
            for result, rating in zip(results, ratings):
                result.score = (result.score + (rating / 10)) / 2
            
            # Sort by new scores
            return sorted(results, key=lambda x: x.score, reverse=True)
            
        except Exception as e:
            logger.warning(f"Result reranking failed: {str(e)}")
            return results
    
    def _combine_similar_results(self, results: List[Any]) -> List[Any]:
        """Combine results with very similar content"""
        combined = []
        seen_content = set()
        
        for result in results:
            content_hash = self._get_content_hash(result.content)
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                combined.append(result)
            else:
                # Update score of existing similar result
                existing = next(r for r in combined 
                              if self._get_content_hash(r.content) == content_hash)
                existing.score = max(existing.score, result.score)
        
        return combined
    
    def _combine_hybrid_results(
        self,
        semantic_results: List[Dict],
        keyword_results: List[Dict],
        weights: Dict[str, float]
    ) -> List[Dict]:
        """Combine and score results from different search methods"""
        combined = {}
        
        # Process semantic results
        for result in semantic_results:
            key = self._get_content_hash(result["content"])
            combined[key] = {
                **result,
                "final_score": result["score"] * weights["semantic"]
            }
        
        # Process keyword results
        for result in keyword_results:
            key = self._get_content_hash(result["content"])
            if key in combined:
                combined[key]["final_score"] += result["score"] * weights["keyword"]
            else:
                combined[key] = {
                    **result,
                    "final_score": result["score"] * weights["keyword"]
                }
        
        # Sort by final score
        return sorted(
            combined.values(),
            key=lambda x: x["final_score"],
            reverse=True
        )
    
    def _get_content_hash(self, content: str) -> str:
        """Get normalized hash of content for deduplication"""
        return str(hash(content.lower().strip()))
    
    def _format_results_for_reranking(self, results: List[Any]) -> str:
        """Format results for LLM reranking"""
        return "\n\n".join(
            f"Result {i+1}:\n{r.content[:200]}..."
            for i, r in enumerate(results)
        )
    
    def _parse_ratings(self, response: str) -> List[float]:
        """Parse LLM ratings response"""
        try:
            import json
            ratings = json.loads(response)
            if isinstance(ratings, list):
                return [float(r) for r in ratings]
            return []
        except Exception:
            return [] 