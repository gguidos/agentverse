import os
from fastapi import UploadFile
from src.core.infrastructure.aws.s3 import S3Client
from src.core.infrastructure.crypto.md5 import compute_md5
import logging

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