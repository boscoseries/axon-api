from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_model: str = "groq/llama3-70b-8192"
    llm_available_models: str = (
        "groq/llama3-8b-8192,groq/llama3-70b-8192,groq/mixtral-8x7b-32768,"
        "openai/gpt-4o,openai/gpt-4o-mini,openai/gpt-oss-120b,"
        "anthropic/claude-opus-4-8,anthropic/claude-sonnet-4-6,anthropic/claude-haiku-4-5-20251001"
    )
    api_key: str = "testkey"
    app_env: str = "development"
    max_file_size_mb: int = 10

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    admin_emails: str = ""

    # AWS / DynamoDB
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"

    # Tables
    dynamo_counts_table: str = "axon-request-counts"
    dynamo_logs_table: str = "axon-request-logs"

    free_requests_limit: int = 3

    # Pinecone / RAG
    pinecone_api_key: str = ""
    pinecone_index: str = ""
    pinecone_top_k: int = 5
    hf_api_key: str = ""
    hf_embedding_model: str = "thenlper/gte-large"

    class Config:
        env_file = ".env"


settings = Settings()