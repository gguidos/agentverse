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
        """
        Check if a file with the given checksum exists in the specified directory of the bucket.
        """
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name

            try:
                # Compute MD5 of the file
                self.logger.info(f"Computing MD5 for file: {file.filename}")
                ref_checksum = self.compute_md5(temp_file_path)
                self.logger.info(f"Computed checksum: {ref_checksum}")
                
                # List files in the specified directory with prefix
                prefix = f"{store_name}/"  # Use store_name as prefix
                self.logger.info(f"Listing files in bucket: {self.bucket_name} with prefix: {prefix}")
                files = self.s3_client.list_files(self.bucket_name, prefix=prefix)
                
                if files is None:
                    self.logger.error("list_files returned None")
                    return False

                if not files:
                    self.logger.info(f"No files found in bucket {self.bucket_name}")
                    return False

                self.logger.info(f"Found {len(files)} files in bucket: {files}")
                
                for key in files:
                    if key.endswith('/'):
                        continue

                    self.logger.info(f"Checking metadata for file: {key}")
                    metadata = self.s3_client.get_file_metadata(self.bucket_name, key)
                    self.logger.info(f"Metadata for {key}: {metadata}")
                    
                    if metadata is None:
                        self.logger.warning(f"get_file_metadata returned None for {key}")
                        continue
                        
                    checksum = metadata.get('md5hash')

                    if not checksum:
                        self.logger.warning(f"File {key} does not have an 'md5' checksum in metadata")
                        continue

                    self.logger.info(f"Comparing checksums for {key}: {checksum} vs {ref_checksum}")
                    if checksum == ref_checksum:
                        self.logger.info(f"Duplicate found: File {key} matches the checksum")
                        return True

                self.logger.info("No duplicate found")
                return False

            finally:
                # Clean up the temporary file
                os.unlink(temp_file_path)
                # Reset file pointer for future reads
                await file.seek(0)

        except Exception as e:
            self.logger.error(f"Error checking for duplicates: {str(e)}")
            self.logger.exception("Full traceback:")
            raise
