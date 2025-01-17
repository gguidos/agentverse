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
from typing import Optional, Any
from fastapi import Depends
from src.core.agentverse.llm import get_llm
from src.core.repositories.agent_repository import AgentRepository
from src.core.services.agent_service import AgentService
from src.core.agentverse.tools.registry import tool_registry
from src.core.agentverse.capabilities import register_default_tools
from src.core.agentverse.memory.vectorstore import VectorstoreService
from src.core.agentverse.memory.agent_memory import AgentMemoryStore
from src.core.services.tool_service import ToolService

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # Add LLM configuration with defaults
    config.llm.from_dict({
        "type": "mock",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "max_tokens": 1000
    })
    
    # Add explicit configuration for AWS
    config.aws.documents_bucket.from_env("AWS_DOCUMENTS_BUCKET")

    # Add MongoDB configuration
    config.mongodb.from_dict({
        "uri": "mongodb://mongodb:27017",
        "db_name": "agentverse"
    })

    s3_client = providers.Singleton(
        S3Client,
        region_name=config.aws.region_name,
    )

    # Set up the MongoDB client using a Singleton provider
    mongo_client = providers.Singleton(
        MongoDBClient,
        db_uri=config.mongodb.uri,
        db_name=config.mongodb.db_name
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

    # Add agent repository
    agent_repository = providers.Factory(
        AgentRepository,
        mongo_client=mongo_client
    )

    # LLM Service
    llm_service = providers.Factory(
        get_llm,
        llm_type=config.llm.type,
        model=config.llm.model,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens
    )

    # Vector store dependencies
    vectorstore_service = providers.Factory(
        VectorstoreService,
        embedding_service=embedding_service,
        chroma_db=chroma_db_client
    )

    # Memory store dependencies
    memory_store = providers.Factory(
        AgentMemoryStore,
        redis_client=redis_client,
        vectorstore=vectorstore_service
    )

    # Tool registry with only required dependencies for simple tools
    tool_registry = providers.Singleton(
        register_default_tools
    )

    agent_service = providers.Factory(
        AgentService,
        agent_repository=agent_repository,
        tool_registry=tool_registry
    )

    tool_service = providers.Factory(
        ToolService,
        tool_registry=tool_registry
    )

async def get_llm_service() -> Any:
    """Get LLM service instance"""
    container = Container()
    llm_config = container.config.llm()
    return get_llm(
        llm_type=llm_config.get("type"),
        **llm_config
    )

async def get_agent_repository() -> AgentRepository:
    """Get agent repository instance"""
    container = Container()
    return container.agent_repository()

async def get_agent_service() -> AgentService:
    """Get agent service instance"""
    container = Container()
    return container.agent_service()

async def get_tool_service() -> ToolService:
    """Get tool service instance"""
    container = Container()
    return container.tool_service()

