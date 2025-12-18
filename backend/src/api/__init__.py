"""
API routes for the Physical AI RAG Backend.
"""

from .chat import router as chat_router
from .ingest import router as ingest_router
from .voice import router as voice_router
from .rag import router as rag_router

__all__ = ["chat_router", "ingest_router", "voice_router", "rag_router"]
