from langchain_aws import BedrockEmbeddings
import os
import boto3
import logging

logger = logging.getLogger(__name__)

class GetEmbeddings:
    def __init__(self):
        self.region_name = os.getenv("AWS_REGION", "eu-central-1")
        self.credentials = {
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        }

    def get_embedding_function(self):
        """Get the embedding function from AWS Bedrock"""
        try:
            boto3_bedrock = boto3.client(
                service_name="bedrock-runtime",
                region_name=self.region_name,
                aws_access_key_id=self.credentials["aws_access_key_id"],
                aws_secret_access_key=self.credentials["aws_secret_access_key"],
            )

            embeddings = BedrockEmbeddings(
                client=boto3_bedrock,
                model_id="amazon.titan-embed-text-v1"
            )
            
            return embeddings
        except Exception as e:
            logger.error(f"Failed to get embedding function: {str(e)}")
            raise