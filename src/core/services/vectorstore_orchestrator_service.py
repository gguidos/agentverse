import os
from fastapi import UploadFile, HTTPException, status
from typing import Dict, Any, List
from src.core.services.check_duplicate import CheckDuplicateService
import logging
from langchain.schema.document import Document
from src.core.services.indexing import IndexingService
from src.core.services.upload_file import UploadService

logger = logging.getLogger(__name__)

class VectorstoreOrchestratorService:
    def __init__(
        self,
        check_duplicate: CheckDuplicateService,
        indexing_service: IndexingService,
        upload_service: UploadService,
    ):
        self.check_duplicate = check_duplicate
        self.indexing_service = indexing_service
        self.upload_service = upload_service

    async def process_file(self, file: UploadFile, store_name: str) -> None:
        """Process and index a file"""
        try:
            logger.info(f"Processing file {file.filename} for store {store_name}")
            
            # Create temp file
            temp_file_path = os.path.join('/tmp', file.filename)
            
            # Save uploaded file content
            content = await file.read()
            with open(temp_file_path, 'wb') as f:
                f.write(content)
                
            # Create document with metadata
            document = Document(
                page_content=temp_file_path,  # This is the issue - we're passing the path as content
                metadata={
                    "filename": file.filename,
                    "store": store_name
                }
            )
            
            # Check for duplicates
            is_duplicate = await self.check_duplicate.check(document, store_name)
            if is_duplicate:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Document already exists in store"
                )
                
            # Index document
            await self.indexing_service.index_documents(store_name, [temp_file_path])  # Changed this line
            
            # # Upload to S3
            # await self.upload_service.upload(temp_file_path, file.filename, store_name)
            
        except Exception as e:
            logger.error(f"Error in file processing: {str(e)}")
            raise
        finally:
            # Cleanup temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.debug(f"Cleaned up temporary file: {temp_file_path}")

    async def list_stores(self) -> List[Dict[str, Any]]:
        """List all vector stores"""
        try:
            logger.debug("Attempting to list vector stores")
            
            # Get list of buckets
            bucket_name = os.getenv('AWS_DOCUMENTS_BUCKET')
            if not bucket_name:
                logger.error("AWS_DOCUMENTS_BUCKET environment variable is not set")
                raise ValueError("AWS_DOCUMENTS_BUCKET environment variable is not set")
            
            logger.debug(f"Using bucket: {bucket_name}")
            
            # List directories (stores) in the bucket
            stores = []
            try:
                # Get list of "directories" from S3
                prefixes = await self.upload_service.list_stores()
                logger.debug(f"Found stores: {prefixes}")
                
                for prefix in prefixes:
                    store_info = {
                        "name": prefix.rstrip('/'),
                        "document_count": await self.get_store_document_count(prefix)
                    }
                    stores.append(store_info)
                    
                logger.debug(f"Processed store information: {stores}")
                return stores
                
            except Exception as e:
                logger.error(f"Error listing stores from S3: {str(e)}", exc_info=True)
                raise
                
        except Exception as e:
            logger.error(f"Error listing vector stores: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list vector stores: {str(e)}"
            )

    async def get_store_document_count(self, store_prefix: str) -> int:
        """Get the number of documents in a store"""
        try:
            # Get count of files in the store directory
            count = await self.upload_service.get_store_document_count(store_prefix)
            return count
        except Exception as e:
            logger.error(f"Error getting document count for store {store_prefix}: {str(e)}")
            return 0

    async def get_store_details(self, store_name: str) -> Dict[str, Any]:
        """Get details about a specific vector store"""
        try:
            logger.debug(f"Getting details for store {store_name}")
            
            # Get document count
            document_count = await self.get_store_document_count(store_name)
            
            # Get collection info from ChromaDB
            collection_info = await self.indexing_service.get_collection_info(store_name)
            
            store_details = {
                "name": store_name,
                "document_count": document_count,
                "chunk_count": collection_info.get("chunk_count", 0),
                "last_updated": collection_info.get("last_updated"),
                "metadata": collection_info.get("metadata", {})
            }
            
            return store_details
            
        except Exception as e:
            logger.error(f"Error getting store details: {str(e)}")
            raise