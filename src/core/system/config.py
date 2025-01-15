from dotenv import load_dotenv

load_dotenv()

def load_config(container):
    # Database configurations
    container.config.db_uri.from_env("MONGO_URI")
    container.config.db_name.from_env("DB_NAME")
    container.config.db_collection.from_env("DB_COLLECTION")
    
    # Redis configurations
    container.config.redis_host.from_env("REDIS_HOST", "redis")
    container.config.redis_port.from_env("REDIS_PORT", "6379")
    container.config.redis_db.from_env("REDIS_DB", "0")
    container.config.redis_password.from_env("REDIS_PASSWORD", default=None)
    container.config.redis_url.from_env("REDIS_URL")
    container.config.redis_session_key_prefix.from_env("REDIS_SESSION_KEY_PREFIX")
    
    # RabbitMQ configurations
    container.config.rabbitmq_host.from_env("RABBITMQ_HOST")
    container.config.rabbitmq_port.from_env("RABBITMQ_PORT")
    container.config.rabbitmq_user.from_env("RABBITMQ_USER")
    container.config.rabbitmq_pass.from_env("RABBITMQ_PASS")
    
    # API configurations
    container.config.api_key.from_env("API_KEY")
    container.config.log_level.from_env("LOG_LEVEL")
    container.config.port.from_env("PORT")
    
    # Storage configurations
    container.config.data_dir.from_env("DATA_DIR")
    container.config.chroma_path.from_env("CHROMA_PATH")
    
    # OpenAI configurations
    container.config.openai_api_key.from_env("OPENAI_API_KEY")
    container.config.system_prompt.from_env("SYSTEM_PROMPT", "You are a helpful assistant.")
    
    # AWS configurations
    container.config.aws_access_key_id.from_env("AWS_ACCESS_KEY_ID")
    container.config.aws_secret_access_key.from_env("AWS_SECRET_ACCESS_KEY")
    container.config.aws_region.from_env("AWS_REGION")
    container.config.aws_documents_bucket.from_env("AWS_DOCUMENTS_BUCKET")
    container.config.aws_data_bucket.from_env("AWS_DATA_BUCKET")
    
    # Memory configurations
    container.config.memory_reflection_threshold.from_env(
        "MEMORY_REFLECTION_THRESHOLD", 
        "10"
    )
    container.config.memory_max_size.from_env(
        "MEMORY_MAX_SIZE", 
        "1000"
    )
    container.config.memory_importance_threshold.from_env(
        "MEMORY_IMPORTANCE_THRESHOLD", 
        "0.7"
    )
    
    # Reflection configurations
    container.config.reflection_threshold.from_env(
        "REFLECTION_THRESHOLD", 
        "10"
    )
    container.config.reflection_memory_window.from_env(
        "REFLECTION_MEMORY_WINDOW", 
        "100"
    )
    container.config.reflection_min_importance.from_env(
        "REFLECTION_MIN_IMPORTANCE", 
        "0.7"
    )
    
    # Summary configurations
    container.config.summary_interval.from_env(
        "SUMMARY_INTERVAL", 
        "10"  # Messages between summaries
    )
    container.config.summary_max_length.from_env(
        "SUMMARY_MAX_LENGTH", 
        "500"  # Max summary length
    )
    
    # Memory configurations
    container.config.memory_type.from_env(
        "MEMORY_TYPE",
        "vectorstore"  # or "simple" or "persistent"
    )
    
    container.config.memory_manipulators.from_env(
        "MEMORY_MANIPULATORS",
        "summary,reflection"  # Comma-separated list
    )
    
    # Manipulator configurations
    container.config.summary_interval.from_env(
        "SUMMARY_INTERVAL",
        "10"
    )
    
    container.config.reflection_interval.from_env(
        "REFLECTION_INTERVAL",
        "20"
    )
    
    # Message configurations
    container.config.message_history_size.from_env(
        "MESSAGE_HISTORY_SIZE",
        "1000"
    )
    container.config.message_broadcast.from_env(
        "MESSAGE_BROADCAST",
        "False"  # Whether to broadcast messages to all agents
    )
    
    # Evaluation configurations
    container.config.evaluation_type.from_env(
        "EVALUATION_TYPE",
        "per_agent"  # or "conversation"
    )
    container.config.evaluation_metrics.from_env(
        "EVALUATION_METRICS",
        "coherence,relevance,accuracy"  # Comma-separated metrics
    )
    
    # Environment configurations
    container.config.order_type.from_env(
        "ORDER_TYPE",
        "sequential"  # or "random" or "concurrent"
    )
    
    container.config.environment.from_dict({
        "max_turns": 10,
        "order": {
            "skip_unavailable": True,
            "batch_size": 2,
            "track_metrics": True
        }
    })
