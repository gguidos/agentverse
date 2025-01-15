import os
from fastapi import UploadFile, HTTPException, status
from typing import Dict, Any
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

    async def process_file(self, file: UploadFile, store_name: str) -> Dict[str, Any]:
        """Process a file for the vector store"""
        try:
            # Save uploaded file temporarily
            temp_path = f"/tmp/{file.filename}"
            
            with open(temp_path, "wb") as temp_file:
                content = await file.read()
                temp_file.write(content)

            try:
                # Check for duplicates
                is_duplicate = await self.check_duplicate.check(file, store_name)
                if is_duplicate:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="File already exists in the store"
                    )

                # Prepare the document for indexing
                document = Document(
                    page_content=temp_path, 
                    metadata={
                        "id": file.filename,
                        "store_name": store_name
                    }
                )

                # Index the document
                await self.indexing_service.index_documents(store_name, [document])

                # Upload the file
                result = await self.upload_service.upload(
                    temp_path,
                    file.filename,
                    store_name
                )

                return {
                    "status": "success",
                    "store_name": store_name,
                    "location": result
                }

            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.debug(f"Cleaned up temporary file: {temp_path}")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process file: {str(e)}"
            )