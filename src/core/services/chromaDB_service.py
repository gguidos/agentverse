import re
from pypdf import PdfReader
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class ChromaDBService:
    """Service for processing and indexing documents"""
    
    def __init__(self, chroma_db, split_document, calculate_chunk_ids, embeddings_client):
        self.chroma_db = chroma_db
        self.split_document = split_document
        self.calculate_chunk_ids = calculate_chunk_ids
        self.embeddings_client = embeddings_client
        logger.info("Initialized indexing service")

    async def index_documents(
            self,
            store_name: str,
            chunks,
            chunk_ids,
            embeddings
    ) -> None:
        """Index documents (including PDF) into the vector store."""
        try:
            logger.debug(f"Indexing documents into store {store_name}")

            # Check for duplicates
            existing_ids = await self.get_existing_ids(store_name, chunk_ids)

            new_chunks, new_ids, new_embeddings = [], [], []
            for chunk, cid, emb in zip(chunks, chunk_ids, embeddings):
                if cid not in existing_ids:
                    new_chunks.append(chunk)
                    new_ids.append(cid)
                    new_embeddings.append(emb)

            if new_chunks:
                # Prepare metadata
                metadatas = [
                    {
                        "store": store_name,
                        "chunk_id": chunk_id
                    }
                    for chunk_id in new_ids
                ]

                # Store in Chroma
                await self.chroma_db.add(
                    collection_name=store_name,
                    ids=new_ids,
                    embeddings=new_embeddings,
                    documents=new_chunks,
                    metadatas=metadatas
                )

                logger.info(f"Successfully indexed {len(new_chunks)} chunks to {store_name}")
            else:
                logger.info(f"No new chunks to index for {store_name}")

        except Exception as e:
            logger.error(f"Error indexing documents: {e}", exc_info=True)
            raise

    async def get_existing_ids(self, store_name: str, chunk_ids: List[str]) -> set:
        """Return the set of chunk IDs that already exist in the store."""
        try:
            collection = await self.chroma_db.get_collection(store_name)
            if not collection:
                return set()  # No collection => no IDs

            existing = collection.get(ids=chunk_ids)  
            
            # existing is a dict, so access the "ids" key:
            ids_list = existing.get("ids", [])
            return set(ids_list)

        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}", exc_info=True)
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
