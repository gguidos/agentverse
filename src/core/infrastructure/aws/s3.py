import boto3
import os
from typing import Dict, Any, List
from botocore.config import Config
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self, region_name: str = None):
        try:
            # Get credentials from environment
            access_key = os.getenv('AWS_ACCESS_KEY_ID')
            secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            region = region_name or os.getenv('AWS_REGION', 'us-east-1')  # Default to us-east-1
            
            # Debug logging
            logger.debug(f"Initializing S3 client with region: {region}")
            logger.debug(f"Access key present: {bool(access_key)}")
            logger.debug(f"Secret key present: {bool(secret_key)}")
            
            # Create client with explicit credentials and config
            config = Config(
                region_name=region,
                signature_version='s3v4',
                retries={'max_attempts': 3},
                s3={'addressing_style': 'virtual'}  # Use virtual-hosted style addressing
            )
            
            self.client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region,
                config=config
            )
            
            # Test connection by listing buckets
            self.client.list_buckets()
            logger.info("Successfully initialized S3 client and verified credentials")
            
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise

    def list_files(self, bucket_name: str, prefix: str = '') -> List[str]:
        """List files in a bucket with an optional prefix (directory)"""
        try:
            # Ensure prefix ends with '/' if it's not empty
            if prefix and not prefix.endswith('/'):
                prefix = f"{prefix}/"

            logger.debug(f"Listing files in bucket: {bucket_name} with prefix: {prefix}")
            results = self.client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            files = []

            if 'Contents' in results:
                for obj in results['Contents']:
                    files.append(obj['Key'])
            return files
            
        except self.client.exceptions.ClientError as e:
            logger.error(f"Error listing files in bucket {bucket_name}: {str(e)}")
            raise

    def get_file_metadata(self, bucket_name: str, key: str) -> Dict[str, str]:
        """Get metadata for a specific file in the bucket"""
        try:
            response = self.client.head_object(Bucket=bucket_name, Key=key)
            return response.get('Metadata', {})
        except self.client.exceptions.ClientError as e:
            logger.error(f"Error getting metadata for {key} in bucket {bucket_name}: {str(e)}")
            raise

    def ensure_directory_exists(self, bucket_name: str, directory: str) -> None:
        """Ensure a directory exists in the bucket by creating an empty marker object"""
        try:
            # Ensure directory ends with '/'
            if not directory.endswith('/'):
                directory = f"{directory}/"

            # Check if directory marker already exists
            try:
                self.client.head_object(Bucket=bucket_name, Key=directory)
                logger.debug(f"Directory {directory} already exists in bucket {bucket_name}")
                return
            except self.client.exceptions.ClientError as e:
                if e.response['Error']['Code'] != '404':
                    raise

            # Create directory marker
            self.client.put_object(Bucket=bucket_name, Key=directory)
            logger.info(f"Created directory {directory} in bucket {bucket_name}")

        except self.client.exceptions.ClientError as e:
            logger.error(f"Error ensuring directory exists {directory} in bucket {bucket_name}: {str(e)}")
            raise

    def upload_file(
            self,
            bucket_name: str,
            file_path: str,
            key: str,
            directory: str = None,
            metadata: Dict[str, str] = None
        ) -> Dict[str, str]:
        """Upload a file to S3, optionally within a directory"""
        try:
            # If directory is specified, ensure it exists and prepend to key
            if directory:
                self.ensure_directory_exists(bucket_name, directory)
                if not directory.endswith('/'):
                    directory = f"{directory}/"
                key = f"{directory}{key}"

            # Prepare upload arguments
            extra_args = {'Metadata': metadata} if metadata else {}

            # Upload the file
            self.client.upload_file(
                Filename=file_path,
                Bucket=bucket_name,
                Key=key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Successfully uploaded {key} to bucket {bucket_name}")
            return {
                "bucket": bucket_name,
                "key": key,
                "status": "uploaded"
            }

        except ClientError as e:
            logger.error(f"Error uploading {key} to bucket {bucket_name}: {str(e)}")
            raise