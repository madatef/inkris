from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "inkris"
    PORT: int = 8000
    DEBUG: bool = False
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024 # 50 MB hard limit
    APP_ENVIRONMENT: str = "dev"
    
    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    AGENT_STATE_DATABASE_URL: str
    AGENT_STATE_DATABASE_URL_ASYNC: str

    SECRET_KEY: str
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"
    ACCESS_TOKEN_COOKIE_NAME: str = "access_token"
    COOKIE_SECURE: bool = True
    TOKENS_COOKIE_PATH : str = "/api"
    TOKENS_COOKIE_SAMESITE: str = "lax"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    ALGORITHM: str = "HS256"

    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"
    EVENTS_BROKER_URL: str = "redis://redis:6379/2"

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = 'eu-central-1'
    AWS_S3_BUCKET: str = 'inkris-files'
    AWS_S3_MEDIA_BUCKET: str = 'inkris-media'

    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION: str

    OPENAI_API_KEY: str
    ORCHESTRATOR_OPENAI_MODEL: str = 'gpt-5.2'
    RAG_OPENAI_MODEL: str = 'gpt-4o-mini'
    SUMMARIZATION_OPENAI_MODEL: str = 'gpt-4o-mini'

    JINA_API_KEY: str
    SERPER_API_KEY: str

    LANGCHAIN_API_KEY: str
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_PROJECT: str = "inkris-agent-monitoring"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    class Config:
        env_file = ".env"

settings = Settings()
