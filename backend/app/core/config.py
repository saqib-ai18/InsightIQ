from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    APP_NAME: str = "InsightIQ"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    DATABASE_URL: str = "sqlite:///./data/insightiq.db"
    DUCKDB_PATH: str = "./data/analytics.duckdb"

    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: str = "csv,xlsx,xls,json,parquet"

    LLM_PROVIDER: str = "openai-compatible"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT: int = 60

    DEFAULT_CHUNK_SIZE: int = 10000
    PROFILING_SAMPLE_SIZE: int = 10000
    QUERY_TIMEOUT_SECONDS: int = 30

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Cloudflare R2
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "insightiq-datasets"
    R2_PUBLIC_URL: str = ""

    # NVIDIA NIM rate limiting
    NVIDIA_RATE_LIMIT_REQUESTS: int = 60
    NVIDIA_RATE_LIMIT_WINDOW_SECONDS: int = 60

    # File processing limits
    MAX_DATASET_ROWS: int = 100000
    MAX_CONCURRENT_ANALYTICS: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()