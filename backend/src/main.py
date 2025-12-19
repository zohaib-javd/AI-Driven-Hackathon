"""
FastAPI application entry point for the Physical AI RAG Backend.

SECURITY FEATURES:
- Fail-fast credential validation on startup
- Sanitized error responses (no internal details exposed)
- Structured logging (never logs credentials)
- CORS configured for specific origins only
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import (
    get_settings,
    validate_credentials_on_startup,
    check_credential_health,
    MissingCredentialError,
)
from .api import chat_router, ingest_router, voice_router, rag_router

# Configure logging - NEVER log credential values
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager with fail-fast credential validation.

    SECURITY: This will exit the application immediately if any
    required credential is missing. The server will NOT start
    without valid credentials.
    """
    logger.info("=" * 60)
    logger.info("Starting Physical AI RAG Backend...")
    logger.info("=" * 60)

    # CRITICAL: Validate all credentials FIRST
    # This will exit the application if any are missing
    logger.info("Validating required credentials...")
    validate_credentials_on_startup()

    # Only proceed if credentials are valid
    settings = get_settings()
    logger.info(f"App: {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"CORS origins: {settings.cors_origins}")

    # Initialize services (only after credentials validated)
    try:
        from .services import get_vectorstore_service
        vectorstore = get_vectorstore_service()
        await vectorstore.initialize_collection_async()
        logger.info("Vector store initialized successfully")
    except Exception as e:
        # Log error but don't expose details
        logger.error(f"Failed to initialize vector store: {type(e).__name__}")
        logger.error("Check your Qdrant credentials and connectivity")
        # Don't exit - let the health check report this

    logger.info("=" * 60)
    logger.info("Backend started successfully")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Shutting down Physical AI RAG Backend...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Don't validate credentials here - do it in lifespan
    # This allows us to still load the app for testing
    try:
        settings = get_settings()
    except MissingCredentialError:
        # Use defaults for app creation, validation happens in lifespan
        class DefaultSettings:
            app_name = "Physical AI RAG Chatbot"
            app_version = "1.0.0"
            cors_origins_list = ["http://localhost:3000"]
        settings = DefaultSettings()

    app = FastAPI(
        title=getattr(settings, 'app_name', 'Physical AI RAG Chatbot'),
        version=getattr(settings, 'app_version', '1.0.0'),
        description="""
# Physical AI & Humanoid Robotics RAG API

AI-powered chatbot for the Physical AI textbook, providing:

- **RAG-powered Q&A** about ROS 2, Gazebo, Isaac Sim, and VLA
- **Selection-only mode** for explaining highlighted text
- **Semantic search** across all book content
- **Voice command processing** with Whisper integration

## Security Features

- All credentials loaded from environment variables
- Fail-fast validation on startup
- Frontend has zero access to API keys
- Sanitized error responses

## Modes

1. **Book Mode** - Full RAG with Qdrant vector search
2. **Selection-Only Mode** - Uses ONLY user-highlighted text (no Qdrant)
        """,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware - only allow specific origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, 'cors_origins_list', ["http://localhost:3000"]),
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "Authorization"],
    )

    # Include routers
    app.include_router(chat_router)
    app.include_router(ingest_router)
    app.include_router(voice_router)
    app.include_router(rag_router)

    # Health check endpoint with credential status
    @app.get("/health")
    async def health_check():
        """
        Health check endpoint with credential validation status.

        Returns credential health without exposing actual values.
        """
        credential_health = check_credential_health()

        # Check service connectivity
        services_status = {
            "qdrant": False,
            "openai": False,
            "cohere": False,
        }

        if credential_health["status"] == "healthy":
            try:
                from .services import get_vectorstore_service
                vs = get_vectorstore_service()
                vs.get_collection_info()
                services_status["qdrant"] = True
            except Exception:
                pass

            # Mark as configured (actual connectivity check is expensive)
            services_status["openai"] = credential_health.get("openai_configured", False)
            services_status["cohere"] = credential_health.get("cohere_configured", False)

        return {
            "status": "healthy" if credential_health["status"] == "healthy" else "unhealthy",
            "app": getattr(settings, 'app_name', 'Physical AI RAG Chatbot'),
            "version": getattr(settings, 'app_version', '1.0.0'),
            "credentials": credential_health,
            "services": services_status,
        }

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": getattr(settings, 'app_name', 'Physical AI RAG Chatbot'),
            "version": getattr(settings, 'app_version', '1.0.0'),
            "docs": "/docs",
            "health": "/health",
            "endpoints": {
                "rag_query": "/api/rag/query",
                "rag_selection": "/api/rag/query-selection",
                "rag_stats": "/api/rag/stats",
            }
        }

    # Global exception handler - SECURITY: Never expose internal errors
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Global exception handler that sanitizes all error responses.

        SECURITY: This handler ensures that internal error details,
        stack traces, and credential information are never exposed
        to clients.
        """
        # Log the full error internally for debugging
        logger.error(f"Unhandled exception on {request.url.path}: {type(exc).__name__}")
        logger.error(f"Error details (internal only): {str(exc)}")

        # Return sanitized error to client
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "Service temporarily unavailable. Please try again.",
                "detail": None,  # Never expose internal details
            },
        )

    # Specific handler for missing credentials
    @app.exception_handler(MissingCredentialError)
    async def credential_error_handler(request: Request, exc: MissingCredentialError):
        """Handle missing credential errors."""
        logger.critical(f"Credential error during request: {str(exc)}")
        return JSONResponse(
            status_code=503,
            content={
                "error": "service_unavailable",
                "message": "The service is not properly configured. Please contact the administrator.",
                "detail": None,
            },
        )

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    # Validate credentials before starting
    validate_credentials_on_startup()

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
