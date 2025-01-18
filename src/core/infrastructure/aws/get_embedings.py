from langchain_aws import BedrockEmbeddings
import os
import boto3
import logging
from typing import List, Union
import numpy as np

logger = logging.getLogger(__name__)

class GetEmbeddings:
    def __init__(self):
        self.region_name = os.getenv("AWS_REGION", "eu-central-1")
        self.credentials = {
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        }
        self.use_mock = os.getenv("USE_MOCK_EMBEDDINGS", "false").lower() == "true"

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
            logger.info('embeddings returned _____________________________________________________')
            return embeddings
        except Exception as e:
            logger.error(f"Failed to get embedding function: {str(e)}")
            raise

    def get_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """Get embeddings for texts - uses mock if configured"""
        if self.use_mock:
            return self._get_mock_embeddings(texts)
        return self._get_aws_embeddings(texts)

    def _get_mock_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """Mock embeddings for testing"""
        if isinstance(texts, str):
            texts = [texts]
            
        # Keep using 384 dimensions to match existing collection
        return [
            list(np.random.uniform(-1, 1, 384)) 
            for _ in texts
        ]

    def _get_aws_embeddings(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """Get real embeddings from AWS"""
        embeddings = self.get_embedding_function()
        if isinstance(texts, str):
            texts = [texts]
        return [embeddings.embed_query(text) for text in texts]