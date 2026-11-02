"""Application configuration using Pydantic Settings."""

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings for Patient360."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application Metadata
    PROJECT_NAME: str = "Patient360 Healthcare Intelligence Platform"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"
    DEBUG: bool = True
    DEMO_MODE: bool = True

    # Server Bind Configuration
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    )

    # Security & Authentication
    SECRET_KEY: str = "patient360_development_insecure_secret_key_change_in_production_32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database Configuration (PostgreSQL)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "patient360_user"
    POSTGRES_PASSWORD: str = "patient360_local_password"
    POSTGRES_DB: str = "patient360_db"
    DATABASE_URL: str = "postgresql+psycopg2://patient360_user:patient360_local_password@localhost:5432/patient360_db"

    # Qdrant Vector Database
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_COLLECTION_NAME: str = "patient360_chunks"
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""

    # Embedding Configuration (FastEmbed CPU-optimized)
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSIONS: int = 384

    # LLM Provider Configuration (Multi-Provider Gateway: Mock, Gemini, Ollama)
    LLM_PROVIDER: Literal["mock", "gemini", "ollama", "openai", "claude"] = "mock"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:4b"
    OLLAMA_TIMEOUT_SECONDS: int = 60
    LLM_FALLBACK_TO_MOCK: bool = True
    ALLOW_MOCK_IN_PRODUCTION: bool = False
    STRICT_PRODUCTION_LLM: bool = True
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Document Storage Configuration
    STORAGE_LOCAL_PATH: str = "./storage/documents"
    MAX_UPLOAD_SIZE_MB: int = 25
    MAX_CONTEXT_TOKENS: int = 2000

    # Clinical Safety & Emergency Advisory Configuration
    EMERGENCY_CONTACT_INFO: str = "emergency medical services (e.g., 911 in North America, 112 in the European Union, 999 in the UK / hospital rapid response team)"

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            if self.LLM_PROVIDER == "mock" and not self.ALLOW_MOCK_IN_PRODUCTION:
                raise ValueError("Mock LLM provider is strictly prohibited in production mode. Set LLM_PROVIDER to gemini or ollama.")
            if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY must be configured when LLM_PROVIDER=gemini in production.")
            if self.LLM_FALLBACK_TO_MOCK and not self.ALLOW_MOCK_IN_PRODUCTION:
                self.LLM_FALLBACK_TO_MOCK = False
        return self

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "testing"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def storage_path(self) -> Path:
        path = Path(self.STORAGE_LOCAL_PATH).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path


# Singleton settings instance
settings = Settings()
