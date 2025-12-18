"""
Configuration management for the Physical AI RAG Backend.
Uses pydantic-settings for environment variable validation.
Supports Cohere for embeddings and OpenAI for chat completions.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Physical AI RAG Chatbot"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Database (Neon Postgres)
    database_url: str = "postgresql+asyncpg://localhost/physical_ai"
    database_url_sync: Optional[str] = None

    # Vector Database (Qdrant)
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "book_chunks"

    # Cohere (Embeddings)
    cohere_api_key: str = ""
    cohere_embedding_model: str = "embed-english-v3.0"
    cohere_embedding_dimension: int = 1024

    # OpenAI (Chat Completions)
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4-turbo-preview"
    openai_max_tokens: int = 2048
    openai_temperature: float = 0.7

    # CORS
    cors_origins: str = "http://localhost:3000"

    # RAG Configuration
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5
    similarity_threshold: float = 0.7
    max_context_length: int = 4000

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60

    # Whisper (Voice)
    whisper_model: str = "base"
    enable_voice_input: bool = False

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL for migrations."""
        if self.database_url_sync:
            return self.database_url_sync
        return self.database_url.replace("+asyncpg", "")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
