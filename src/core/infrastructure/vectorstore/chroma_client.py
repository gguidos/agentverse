import chromadb
from chromadb.config import Settings
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ChromaClient:
    def __init__(self, embedding_function):
        """Initialize ChromaDB client with embedding function"""
        from src.core.infrastructure.embeddings.embeddings_client import EmbeddingFunctionWrapper
        
        # Handle the embedding function
        if isinstance(embedding_function, type):  # If it's a class
            embeddings_client = embedding_function(None, None)  # Initialize with None params
        else:
            embeddings_client = embedding_function
            
        self.embeddings_client = EmbeddingFunctionWrapper(embeddings_client)
            
        # Initialize ChromaDB client - Use PersistentClient instead of Client
        self.client = chromadb.PersistentClient(path="./chroma_db")
        
        logger.debug("Initialized ChromaDB client")

    async def add(
        self,
        collection_name: str,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """Add documents to ChromaDB"""
        try:
            # Get or create collection using native ChromaDB API
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embeddings_client
            )
            
            # Add documents using native ChromaDB API
            collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully added {len(documents)} documents to collection {collection_name}")
            
        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {str(e)}")
            raise

    async def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search documents in ChromaDB"""
        try:
            collection = self.client.get_collection(name=collection_name)
            
            # Get query embedding
            query_embedding = self.embedding_function.embed_query(query)
            
            # Search using native ChromaDB API
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {str(e)}")
            raise 

    async def get_collection(self, collection_name: str):
        """Get a collection by name"""
        try:
            return self.client.get_collection(name=collection_name)
        except Exception as e:
            logger.error(f"Error getting collection {collection_name}: {str(e)}")
            return None 