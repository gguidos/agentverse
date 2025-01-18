import os
from fastapi import UploadFile
from src.core.infrastructure.aws.s3 import S3Client
from src.core.infrastructure.crypto.md5 import compute_md5
import logging
from typing import List

logger = logging.getLogger(__name__)

class UploadService:
    def __init__(
        self,
        s3_client: S3Client,
    ):
        self.s3_client = s3_client

    async def upload(self, file_path: str, filename: str, store: str) -> dict:
        try:
            # Compute MD5 hash
            file_md5 = compute_md5(file_path)

            # Get bucket name from environment or configuration
            bucket_name = os.getenv('AWS_DOCUMENTS_BUCKET')
            if not bucket_name:
                raise ValueError("AWS_DOCUMENTS_BUCKET environment variable is not set")

            # Upload to S3 with metadata
            self.s3_client.upload_file(
                bucket_name=bucket_name,
                file_path=file_path,
                key=filename,
                directory=store,
                metadata={'md5hash': file_md5}
            )

            return {
                "filename": filename,
                "bucket": bucket_name,
                "status": "uploaded"
            }

        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise

    async def list_stores(self) -> List[str]:
        """List all stores in S3"""
        try:
            logger.debug("Listing stores from S3")
            result = self.s3_client.list_files(
                bucket=self.documents_bucket,
                prefix="",  # Remove delimiter parameter
            )
            
            # Extract unique prefixes (store names) from the results
            prefixes = set()
            for item in result:
                # Get the first part of the path (store name)
                parts = item.split('/')
                if len(parts) > 1:
                    prefixes.add(parts[0])
            
            return list(prefixes)
            
        except Exception as e:
            logger.error(f"Error listing stores: {str(e)}")
            raise

    async def get_store_document_count(self, store_prefix: str) -> int:
        """Get number of documents in a store"""
        try:
            bucket_name = os.getenv('AWS_DOCUMENTS_BUCKET')
            if not bucket_name:
                raise ValueError("AWS_DOCUMENTS_BUCKET environment variable is not set")
            
            # List objects in the store directory
            result = self.s3_client.list_files(
                bucket_name,
                prefix=store_prefix
            )
            
            # Count only files, not directories
            count = sum(1 for obj in result.get('Contents', []) 
                       if not obj['Key'].endswith('/'))
            return count
            
        except Exception as e:
            logger.error(f"Error getting store document count: {str(e)}")
            raise