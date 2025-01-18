from typing import Dict, Any, Optional, List
from .base import BaseMemory
from .exceptions import MemoryStorageError
import logging

logger = logging.getLogger(__name__)

class VectorstoreMemory(BaseMemory):
    """Memory implementation using vectorstore"""
    
    def __init__(
        self,
        embedding_service: Any,
        chroma_db: Any,
        collection_name: str = "memory",
        session_id: Optional[str] = None
    ):
        """Initialize vectorstore memory
        
        Args:
            embedding_service: Service for generating embeddings
            chroma_db: ChromaDB client
            collection_name: Name of collection to use
            session_id: Optional session ID for scoping memory
        """
        try:
            self.embedding_service = embedding_service
            self.chroma_db = chroma_db
            self.collection_name = collection_name
            self.session_id = session_id
            
            if not embedding_service:
                raise MemoryStorageError("Embedding service is required")
                
            if not chroma_db:
                raise MemoryStorageError("ChromaDB client is required")
                
            logger.info(f"Initialized vectorstore memory with collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"Error initializing vectorstore memory: {str(e)}")
            raise MemoryStorageError(f"Failed to initialize memory: {str(e)}")
            
    async def initialize(self):
        """Initialize memory resources"""
        try:
            # Create collection if it doesn't exist
            await self.chroma_db.create_collection(self.collection_name)
            logger.info(f"Initialized collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error initializing memory: {str(e)}")
            raise MemoryStorageError(f"Failed to initialize memory: {str(e)}")
            
    async def get_context(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get memory context for session"""
        try:
            sid = session_id or self.session_id
            if not sid:
                return {}
                
            collection = await self.chroma_db.get_collection(self.collection_name)
            if not collection:
                return {}
                
            # Get most recent memories for session
            results = await collection.query(
                query_texts=[""],
                n_results=5,
                where={"session_id": sid}
            )
            
            return {
                "memories": results.get("documents", []),
                "metadata": results.get("metadatas", [])
            }
            
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            return {}
            
    async def save_context(self, context: Dict[str, Any], session_id: Optional[str] = None):
        """Save context to memory"""
        try:
            sid = session_id or self.session_id
            if not sid:
                return
                
            collection = await self.chroma_db.get_collection(self.collection_name)
            if not collection:
                return
                
            # Convert context to text
            text = str(context)
            
            # Get embedding
            embedding = await self.embedding_service.get_embeddings([text])
            
            # Add to collection
            await collection.add(
                embeddings=embedding,
                documents=[text],
                metadatas=[{"session_id": sid}],
                ids=[f"{sid}_{context.get('timestamp', '')}"]
            )
            
        except Exception as e:
            logger.error(f"Error saving context: {str(e)}")
            raise MemoryStorageError(f"Failed to save context: {str(e)}") 