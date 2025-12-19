"""
Secure Configuration Management for Physical AI RAG Backend.

SECURITY FEATURES:
- Fail-fast validation on startup
- No hardcoded secrets (all from environment variables)
- Clear error messages identifying missing credentials
- Never logs or exposes credential values
"""

import sys
import logging
from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# List of required credentials that MUST be present
REQUIRED_CREDENTIALS = [
    "cohere_api_key",
    "openai_api_key",
    "qdrant_url",
    "qdrant_api_key",
    "database_url",
]


class MissingCredentialError(Exception):
    """Raised when a required credential is missing."""
    pass


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    SECURITY: Required credentials have no defaults and will cause
    startup failure if not provided via environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =========================================================================
    # REQUIRED CREDENTIALS (No defaults - must be provided)
    # =========================================================================

    # Cohere API Key (for embeddings)
    cohere_api_key: str = ""

    # OpenAI API Key (for chat completions)
    openai_api_key: str = ""

    # Qdrant Cloud credentials
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # Neon Postgres Database URL
    database_url: str = ""

    # =========================================================================
    # OPTIONAL CONFIGURATION (Have sensible defaults)
    # =========================================================================

    # Application
    app_name: str = "Physical AI RAG Chatbot"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    # Database (optional sync URL)
    database_url_sync: Optional[str] = None

    # Qdrant Configuration
    qdrant_collection_name: str = "book_chunks"

    # Cohere Configuration
    cohere_embedding_model: str = "embed-english-v3.0"
    cohere_embedding_dimension: int = 1024

    # OpenAI Configuration
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


def validate_required_credentials(settings: Settings) -> List[str]:
    """
    Validate that all required credentials are present.

    Returns:
        List of missing credential names (empty if all present)
    """
    missing = []

    for credential in REQUIRED_CREDENTIALS:
        value = getattr(settings, credential, "")
        if not value or not value.strip():
            missing.append(credential.upper())

    return missing


def get_settings_safe() -> tuple[Optional[Settings], List[str]]:
    """
    Safely get settings and return any validation errors.

    Returns:
        Tuple of (settings or None, list of missing credentials)
    """
    try:
        settings = Settings()
        missing = validate_required_credentials(settings)
        if missing:
            return None, missing
        return settings, []
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        return None, [str(e)]


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance with fail-fast validation.

    SECURITY: This function will raise an exception and log an error
    if any required credential is missing. The error message will
    identify which credential is missing WITHOUT exposing any values.

    Raises:
        MissingCredentialError: If any required credential is missing
    """
    settings = Settings()
    missing = validate_required_credentials(settings)

    if missing:
        error_msg = f"Missing required credential(s): {', '.join(missing)}"
        logger.critical(error_msg)
        logger.critical("The backend cannot start without all required credentials.")
        logger.critical("Please check your .env file and ensure all credentials are set.")
        logger.critical("See backend/.env.example for the required variables.")
        raise MissingCredentialError(error_msg)

    # Log successful validation (without exposing values)
    logger.info("All required credentials validated successfully")
    logger.info(f"Cohere Model: {settings.cohere_embedding_model}")
    logger.info(f"OpenAI Model: {settings.openai_chat_model}")
    logger.info(f"Qdrant Collection: {settings.qdrant_collection_name}")

    return settings


def validate_credentials_on_startup() -> bool:
    """
    Validate all credentials on application startup.
    Called from the FastAPI lifespan event.

    SECURITY: This function will exit the application if credentials
    are missing. This is the fail-fast behavior required by the constitution.

    Returns:
        True if all credentials are valid

    Raises:
        SystemExit: If any credential is missing
    """
    try:
        settings = get_settings()
        return True
    except MissingCredentialError as e:
        logger.critical("=" * 60)
        logger.critical("STARTUP FAILED: Missing required credentials")
        logger.critical("=" * 60)
        logger.critical(str(e))
        logger.critical("")
        logger.critical("Required credentials:")
        logger.critical("  - COHERE_API_KEY: Cohere API key for embeddings")
        logger.critical("  - OPENAI_API_KEY: OpenAI API key for chat")
        logger.critical("  - QDRANT_URL: Qdrant Cloud URL")
        logger.critical("  - QDRANT_API_KEY: Qdrant API key")
        logger.critical("  - DATABASE_URL: Neon Postgres connection string")
        logger.critical("")
        logger.critical("Please set these in your .env file and restart.")
        logger.critical("=" * 60)
        sys.exit(1)


def check_credential_health() -> dict:
    """
    Check the health of credentials without exposing values.

    Returns:
        Dictionary with credential health status
    """
    settings, missing = get_settings_safe()

    if settings is None:
        return {
            "status": "unhealthy",
            "missing_credentials": missing,
            "message": "Required credentials are missing",
        }

    return {
        "status": "healthy",
        "missing_credentials": [],
        "credentials_validated": True,
        # Never expose actual values - only confirm presence
        "cohere_configured": bool(settings.cohere_api_key),
        "openai_configured": bool(settings.openai_api_key),
        "qdrant_configured": bool(settings.qdrant_url and settings.qdrant_api_key),
        "database_configured": bool(settings.database_url),
    }
