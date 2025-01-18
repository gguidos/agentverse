import os
from fastapi import UploadFile, HTTPException, status
from typing import Dict, Any, List
from src.core.services.check_duplicate import CheckDuplicateService
import logging
from langchain.schema.document import Document
from src.core.services.indexing import IndexingService
from src.core.services.upload_file import UploadService

logger = logging.getLogger(__name__)

class VectorstoreService:
    """Service for managing vector stores"""
    
    def __init__(
        self,
        check_duplicate: CheckDuplicateService,
        indexing_service: IndexingService,
        upload_service: UploadService,
        collection_name: str = "forms"
    ):
        self.check_duplicate = check_duplicate
        self.indexing_service = indexing_service
        self.upload_service = upload_service
        self.collection_name = collection_name
        logger.info(f"Initialized vectorstore service with collection: {collection_name}")

    async def process_file(self, file: UploadFile, store_name: str) -> Dict[str, Any]:
        """Process and store a file in the vector store"""
        try:
            # Validate file content
            content = await file.read()
            if not content:
                raise ValueError("Empty file content")
            
            # Reset file position after validation
            await file.seek(0)
            
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
            await self.upload_service.upload(temp_file_path, file.filename, store_name)
            
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
            collections = await self.indexing_service.list_collections()
            stores = []
            for name in collections:
                info = await self.indexing_service.get_collection_info(name)
                stores.append({
                    "name": name,
                    **info
                })
            return stores
        except Exception as e:
            logger.error(f"Error listing stores: {str(e)}")
            raise

    async def get_store_details(self, store_name: str) -> Dict[str, Any]:
        """Get details about a specific vector store"""
        try:
            info = await self.indexing_service.get_collection_info(store_name)
            return {
                "name": store_name,
                **info
            }
        except Exception as e:
            logger.error(f"Error getting store details: {str(e)}")
            raise