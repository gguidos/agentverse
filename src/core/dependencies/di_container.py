from dependency_injector import containers, providers
from src.core.infrastructure.db.mongo_client import MongoDBClient
from src.core.infrastructure.aws.get_embedings import GetEmbeddings
from src.core.infrastructure.pika import PikaClient
from src.core.repositories.db_repository import DBRepository
from src.core.infrastructure.db.chromadb import ChromaDB
from src.core.repositories.rabbitmq_repository import RabbitMQRepository
from src.core.infrastructure.db.redis_client import RedisClient
from src.core.services.openai_service import OpenAIService
from src.core.services.check_duplicate import CheckDuplicateService
from src.core.infrastructure.aws.s3 import S3Client
from src.core.infrastructure.crypto.md5 import compute_md5, MD5Calculator
from src.core.services.upload_file import UploadService
from src.core.services.vectorstore_orchestrator_service import VectorstoreOrchestratorService
from src.core.services.indexing import IndexingService
from src.core.utils.calculate_chunk_ids import CalculateChunkIds
from src.core.infrastructure.fs.split_document import SplitDocument

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # Add explicit configuration for AWS
    config.aws.documents_bucket.from_env("AWS_DOCUMENTS_BUCKET")

    s3_client = providers.Singleton(
        S3Client,
        region_name=config.aws.region_name,
    )

    # Set up the MongoDB client using a Singleton provider
    mongo_client = providers.Singleton(
        MongoDBClient,
        db_uri=config.db_uri,
        db_name=config.db_name
    )

    # Redis Client (Singleton using the new RedisClient class)
    redis_client = providers.Singleton(
        RedisClient,
        host=config.redis_host,
        port=config.redis_port,
        db=config.redis_db,
        password=config.redis_password
    )

    openai_service = providers.Singleton(OpenAIService)

    embeddings_client = providers.Singleton(
        GetEmbeddings
    )

    split_document_client = providers.Singleton(
        SplitDocument
    )

    calculate_chunk_ids_client = providers.Singleton(
        CalculateChunkIds
    )

    chroma_db_client = providers.Singleton(
        ChromaDB,
        embeddings_client=embeddings_client,
        chroma_path=config.chroma_path
    )

    indexing_service = providers.Singleton(
        IndexingService,
        chroma_db=chroma_db_client,
        split_document=split_document_client,
        calculate_chunk_ids=calculate_chunk_ids_client,
        embeddings_client=embeddings_client
    )
    
    # Memory dependencies
    embedding_service = providers.Singleton(
        GetEmbeddings
    )

    compute_md5 = providers.Singleton(
        MD5Calculator
    )

    check_duplicate_service = providers.Factory(
        CheckDuplicateService,
        s3_client=s3_client,
        compute_md5=compute_md5,
        bucket_name=config.aws.documents_bucket
    )
    
    upload_service = providers.Factory(
        UploadService,
        s3_client=s3_client,
    )
    
    vectorstore_orchestrator_service = providers.Factory(
        VectorstoreOrchestratorService,
        check_duplicate=check_duplicate_service,
        indexing_service=indexing_service,
        upload_service=upload_service
    )

    # RabbitMQ Client (Singleton)
    rabbitmq_client = providers.Singleton(
        PikaClient,
        rabbitmq_host=config.rabbitmq_host
    )

    # RabbitMQ Repository (Factory)
    rabbitmq_repository = providers.Factory(
        RabbitMQRepository,
        pika_client=rabbitmq_client
    )

    # Register UserRepository with the MongoDB client
    db_repository = providers.Factory(
        DBRepository,
        client=mongo_client
    )

    # Consume User Auth Queue use case
    consume_queue = providers.Factory(
        rabbitmq_repository=rabbitmq_repository
    )

