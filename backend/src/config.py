"""
Configuration management for the Physical AI RAG Backend.
Uses pydantic-settings for environment variable validation.
"""

from functools import lru_cache
from typing import List

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

    # Database (Neon Postgres)
    database_url: str

    # Vector Database (Qdrant)
    qdrant_url: str
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "physical_ai_book"

    # OpenAI
    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-large"
    openai_chat_model: str = "gpt-4-turbo-preview"

    # CORS
    cors_origins: str = "http://localhost:3000"

    # RAG Configuration
    chunk_size: int = 500
    chunk_overlap: int = 50
    top_k_results: int = 5
    similarity_threshold: float = 0.7

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
