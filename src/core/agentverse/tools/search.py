from src.core.tools.base import AgentTool, ToolResult
from src.core.infrastructure.db.chromadb import ChromaDB

class SearchTool(AgentTool):
    name = "search"
    description = "Search for information in the knowledge base"
    
    def __init__(self, vector_store: ChromaDB):
        self.vector_store = vector_store
    
    async def execute(self, query: str, top_k: int = 3) -> ToolResult:
        try:
            results = self.vector_store.similarity_search(query, k=top_k)
            return ToolResult(
                success=True,
                result=[doc.page_content for doc in results]
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            ) 