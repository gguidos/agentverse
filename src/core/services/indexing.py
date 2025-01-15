import logging
from langchain.schema.document import Document
from langchain.vectorstores.chroma import Chroma
from src.core.infrastructure.db.chromadb import ChromaDB
from src.core.infrastructure.fs.split_document import SplitDocument
from src.core.infrastructure.aws.get_embedings import GetEmbeddings
from src.core.utils.calculate_chunk_ids import CalculateChunkIds
import os

logger = logging.getLogger(__name__)

class IndexingService:
    def __init__(
            self,
            chroma_db: ChromaDB,
            split_document: SplitDocument,
            calculate_chunk_ids: CalculateChunkIds,
            embeddings_client: GetEmbeddings
    ):
        self.chroma_db = chroma_db
        self.split_document = split_document
        self.calculate_chunk_ids = calculate_chunk_ids
        self.get_embedings = embeddings_client

    async def index_documents(self, store_name: str, documents: list[Document]):
        """Index the provided documents in the specified collection."""
        logger.info(f"Indexing {len(documents)} documents in collection: {store_name}.")
        
        try:
            EMBEDDING = self.get_embedings.get_embedding_function()
            CHROMA_PATH = os.getenv("CHROMA_PATH")
            DB = Chroma(
                collection_name=store_name,
                persist_directory=CHROMA_PATH,
                embedding_function=EMBEDDING
            )
            
            chunks = self.split_document.split_document(documents)

            # Calculate Page IDs.
            chunks_with_ids = self.calculate_chunk_ids.calculate_chunk_ids(chunks)
            existing_items = DB.get(include=[])  # IDs are always included by default
            existing_ids = set(existing_items["ids"])
            
            # Only add documents that don't exist in the DB.
            new_chunks = []
            for chunk in chunks_with_ids:
                if chunk.metadata["id"] not in existing_ids:
                    new_chunks.append(chunk)
            
            if len(new_chunks):
                logger.info(f"Indexed {len(new_chunks)} new documents.")
                new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
                DB.add_documents(new_chunks, ids=new_chunk_ids)
                DB.persist()
            else:
                logger.info("✅ No new documents to add.")
            
            logger.info("Indexing completed.")
        
        except Exception as e:
            logger.error(f"Error during indexing: {str(e)}")
            raise
