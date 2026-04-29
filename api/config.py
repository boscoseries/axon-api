from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str
    llm_model: str = "openai/gpt-oss-120b"
    api_key: str = "testkey"
    app_env: str = "development"
    max_file_size_mb: int = 10

    class Config:
        env_file = ".env"


settings = Settings()