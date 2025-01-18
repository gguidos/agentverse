import boto3
import os
from typing import Dict, Any, List
from botocore.config import Config
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self, region_name: str):
        """Initialize S3 client"""
        self.client = boto3.client('s3', region_name=region_name)
        logger.debug(f"Initializing S3 client with region: {region_name}")
        
    def list_files(self, bucket: str, prefix: str = "") -> List[str]:
        """List files in S3 bucket with given prefix"""
        try:
            paginator = self.client.get_paginator('list_objects_v2')
            files = []
            
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        files.append(obj['Key'])
                        
            return files
            
        except Exception as e:
            logger.error(f"Error listing files from S3: {str(e)}")
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