"""Indexing Service Module"""

from typing import Dict, Any, Optional, List
from langchain_community.vectorstores import Chroma  # Updated import
from langchain.embeddings import OpenAIEmbeddings
import logging

logger = logging.getLogger(__name__)

class IndexingService:
    """Document indexing service"""
    
    def __init__(
        self,
        embedding_model: str = "text-embedding-ada-002",
        persist_directory: str = "./indexes"
    ):
        """Initialize indexing service
        
        Args:
            embedding_model: OpenAI embedding model
            persist_directory: Directory to persist indexes
        """
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.persist_directory = persist_directory
        self.vectorstore = None
        
    async def initialize(self) -> None:
        """Initialize vector store"""
        try:
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            logger.info("Initialized indexing service")
            
        except Exception as e:
            logger.error(f"Indexing service initialization failed: {str(e)}")
            raise
