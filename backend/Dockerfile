# Physical AI RAG Backend Dockerfile
# Multi-stage build for optimized production image
#
# SECURITY NOTICE:
# - NO secrets are baked into this image
# - All credentials MUST be injected at runtime via environment variables
# - The backend will REFUSE TO START without required credentials:
#   - COHERE_API_KEY
#   - OPENAI_API_KEY
#   - QDRANT_URL
#   - QDRANT_API_KEY
#   - DATABASE_URL

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code (NO secrets)
COPY --chown=appuser:appuser src/ ./src/

# Set environment variables (non-sensitive defaults only)
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_NAME="Physical AI RAG Chatbot"
ENV APP_VERSION="1.0.0"
ENV LOG_LEVEL="INFO"

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check - verifies the backend is running and credentials are configured
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
# The backend will validate all credentials on startup and exit if any are missing
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
