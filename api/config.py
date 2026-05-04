from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    llm_model: str = "openai/gpt-oss-120b"
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

    class Config:
        env_file = ".env"


settings = Settings()