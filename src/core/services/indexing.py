import os
from pypdf import PdfReader
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class IndexingService:
    """Service for processing and indexing documents"""
    
    def __init__(self, chroma_db, split_document, calculate_chunk_ids, embeddings_client):
        self.chroma_db = chroma_db
        self.split_document = split_document
        self.calculate_chunk_ids = calculate_chunk_ids
        self.embeddings_client = embeddings_client
        logger.info("Initialized indexing service")

    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from a PDF using pypdf."""
        text = ""
        with open(file_path, "rb") as pdf_file:
            pdf_reader = PdfReader(pdf_file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
        return text

    async def index_documents(self, store_name: str, file_paths: List[str]) -> None:
        """Index documents (including PDF) into the vector store."""
        try:
            logger.debug(f"Indexing documents into store {store_name}")
            
            for file_path in file_paths:
                # Check if PDF
                if file_path.lower().endswith(".pdf"):
                    logger.debug(f"Extracting text from PDF: {file_path}")
                    content = self._extract_pdf_text(file_path)
                else:
                    # Attempt reading as a plain text file
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        with open(file_path, "r", encoding="latin-1") as f:
                            content = f.read()

                content = content.strip()
                
                if not content:
                    logger.warning(f"No text extracted or readable from: {file_path}. Skipping.")
                    continue
                
                # Split content into chunks
                chunks = await self.split_document.split_text(content)
                if not chunks:
                    logger.warning(f"No chunks produced from file: {file_path}. Skipping.")
                    continue

                # Generate unique chunk IDs
                chunk_ids = self.calculate_chunk_ids.calculate(chunks)

                # Get embeddings
                embeddings = self.embeddings_client.get_embeddings(chunks)

                # Prepare metadata
                metadatas = [
                    {
                        "source": file_path,
                        "store": store_name,
                        "chunk_id": chunk_id
                    }
                    for chunk_id in chunk_ids
                ]

                # Store in Chroma
                await self.chroma_db.add(
                    collection_name=store_name,
                    ids=chunk_ids,
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=metadatas
                )

                logger.info(f"Successfully indexed {len(chunks)} chunks for {file_path}")

        except Exception as e:
            logger.error(f"Error indexing documents: {e}", exc_info=True)
            raise

    async def get_collection_info(self, store_name: str) -> Dict[str, Any]:
        """Get information about a collection"""
        try:
            collection = await self.chroma_db.get_collection(store_name)
            if not collection:
                return {
                    "chunk_count": 0,
                    "last_updated": None,
                    "metadata": {}
                }
            
            count = collection.count()
            return {
                "chunk_count": count,
                "last_updated": None,  # Could add timestamp in metadata later
                "metadata": {}         # Could add custom metadata later
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            raise

    async def list_collections(self) -> List[str]:
        """List all collections in ChromaDB"""
        try:
            collections = await self.chroma_db.list_collections()
            logger.info(f"IndexingService - Found collections: {collections}")
            return collections
        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            raise
