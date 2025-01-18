import logging
from src.core.infrastructure.aws.s3 import S3Client
from src.core.infrastructure.crypto.md5 import compute_md5
from fastapi import UploadFile
import os
import tempfile

logger = logging.getLogger(__name__)

class CheckDuplicateService:
    def __init__(
            self,
            s3_client: S3Client,
            compute_md5: compute_md5,
            bucket_name: str
        ):
        if not bucket_name:
            raise ValueError("bucket_name must be provided")
        self.s3_client = s3_client
        self.compute_md5 = compute_md5
        self.logger = logger
        self.bucket_name = bucket_name

    async def check(self, file: UploadFile, store_name: str) -> bool:
        """Check if file already exists in store"""
        try:
            logger.debug(f"Checking for duplicates in store {store_name}")
            # Your duplicate checking logic here
            return False
        except Exception as e:
            logger.error(f"Error checking duplicates: {str(e)}", exc_info=True)
            raise
