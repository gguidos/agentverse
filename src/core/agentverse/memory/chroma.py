from typing import List, Dict, Optional
import uuid
import chromadb
from chromadb.config import Settings
import logging
from src.core.agentverse.memory.base import BaseMemory, Message

logger = logging.getLogger(__name__)

class ChromaDB(BaseMemory):
    def __init__(self, persist_directory: str = "chroma_db"):
        # Initialize base class
        super().__init__()
        
        logger.info(f"Initializing ChromaDB with persist_directory: {persist_directory}")
        
        try:
            self._client = chromadb.Client(
                Settings(
                    persist_directory=persist_directory,
                    is_persistent=True
                )
            )
            
            # Create or get the collection
            self._collection = self._client.get_or_create_collection(
                name="forms",
                metadata={"hnsw:space": "cosine"}  # Using cosine similarity
            )
            
            logger.info("ChromaDB initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}", exc_info=True)
            raise
    
    @property
    def collection(self):
        """Get the underlying ChromaDB collection"""
        if not hasattr(self, '_collection'):
            raise RuntimeError("ChromaDB collection not initialized")
        return self._collection
    
    async def add_documents(self, documents: List[str], metadata: Optional[List[Dict]] = None):
        """Add documents to the vector store"""
        try:
            # Generate IDs for the documents
            ids = [str(uuid.uuid4()) for _ in documents]
            
            # Add documents to the collection
            self._collection.add(
                documents=documents,
                metadatas=metadata or [{}] * len(documents),
                ids=ids
            )
            
            return {"status": "success", "message": f"Added {len(documents)} documents"}
            
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise
            
    async def get_relevant_context(self, query: str, k: int = 5) -> List[str]:
        """Get relevant context for a query"""
        try:
            logger.info(f"Querying ChromaDB with: {query}")
            
            if not self._collection:
                raise RuntimeError("ChromaDB collection not initialized")
                
            results = self._collection.query(
                query_texts=[query],
                n_results=k
            )
            
            logger.info(f"ChromaDB query results: {results}")
            
            if results and results['documents'] and results['documents'][0]:
                return results['documents'][0]
            return []
            
        except Exception as e:
            logger.error(f"Failed to get relevant context: {str(e)}", exc_info=True)
            raise
            
    async def add_message(self, messages: List[Message]) -> None:
        """Add new messages to memory"""
        self.messages.extend(messages)
    
    async def get_messages(self, 
                         start: int = 0, 
                         limit: int = 100,
                         filters: Dict = None) -> List[Message]:
        """Retrieve messages from memory"""
        filtered_messages = self.messages[start:start+limit]
        if filters:
            # Apply filters if provided
            for key, value in filters.items():
                filtered_messages = [m for m in filtered_messages if getattr(m, key, None) == value]
        return filtered_messages
    
    def to_string(self) -> str:
        """Convert memory contents to string"""
        return "\n".join([f"{m.sender}: {m.content}" for m in self.messages])
    
    async def reset(self) -> None:
        """Clear all memory contents"""
        self.messages = []
        # Optionally clear the collection
        self._collection.delete(where={}) 