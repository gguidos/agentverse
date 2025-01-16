"""ChromaDB Infrastructure Module"""

from typing import Dict, Any, Optional, List
from langchain_community.vectorstores import Chroma  # Updated import
import chromadb
import logging

logger = logging.getLogger(__name__)

class ChromaDB:
    """ChromaDB client wrapper"""
    
    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "default"
    ):
        """Initialize ChromaDB client
        
        Args:
            persist_directory: Directory to persist data
            collection_name: Name of collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
    async def connect(self) -> None:
        """Connect to ChromaDB"""
        try:
            # Initialize client
            self.client = chromadb.PersistentClient(
                path=self.persist_directory
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name
            )
            
            logger.info(f"Connected to ChromaDB collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"ChromaDB connection failed: {str(e)}")
            raise