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

    async def check(self, bucket_name: str, file_path: str, directory: str = None) -> bool:
        """
        Check if a file with the given checksum exists in the specified directory of the bucket.
        """
        try:
            # Compute MD5 of the file to be uploaded
            ref_checksum = compute_md5(file_path)

            # List files in the specified directory
            files = self.s3_client.list_files(bucket_name, prefix=directory)

            if not files:
                self.logger.info(f"No files found in {directory or 'root'} of bucket {bucket_name}")
                return False

            for key in files:
                # Skip directory markers
                if key.endswith('/'):
                    continue

                metadata = self.s3_client.get_file_metadata(bucket_name, key)
                checksum = metadata.get('md5hash')

                if not checksum:
                    self.logger.warning(f"File {key} does not have an 'md5' checksum in metadata")
                    continue

                if checksum == ref_checksum:
                    self.logger.info(f"Duplicate found: File {key} matches the checksum")
                    return True

            self.logger.info("No duplicate found")
            return False

        except Exception as e:
            self.logger.error(f"Error checking for duplicates: {str(e)}")
            raise
