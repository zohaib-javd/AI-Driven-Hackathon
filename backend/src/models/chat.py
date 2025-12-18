"""
Chat models for the RAG chatbot.
Defines schemas for chat messages, sessions, and responses.
"""

from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Citation(BaseModel):
    """A citation to source material."""

    document_id: str = Field(..., description="Source document ID")
    chunk_id: str = Field(..., description="Source chunk ID")
    module: str = Field(..., description="Module name")
    chapter: str = Field(..., description="Chapter name")
    chapter_title: str = Field(..., description="Chapter title")
    relevance_score: float = Field(..., description="Similarity score")
    excerpt: str = Field(..., description="Relevant excerpt from source")


class ChatMessage(BaseModel):
    """A single chat message."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    role: MessageRole = Field(..., description="Message sender role")
    content: str = Field(..., description="Message content")
    citations: List[Citation] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatSession(BaseModel):
    """A chat session containing multiple messages."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Session metadata
    title: Optional[str] = Field(None, description="Session title")
    summary: Optional[str] = Field(None, description="Session summary")


class ChatRequest(BaseModel):
    """Request to chat with the RAG system."""

    message: str = Field(..., description="User message", min_length=1, max_length=4000)
    session_id: Optional[str] = Field(None, description="Existing session ID")

    # Options
    include_citations: bool = Field(default=True)
    max_context_chunks: int = Field(default=5, ge=1, le=10)
    temperature: float = Field(default=0.7, ge=0, le=2)

    # Filters
    module_filter: Optional[str] = Field(None, description="Filter to specific module")


class ChatResponse(BaseModel):
    """Response from the RAG chatbot."""

    message: ChatMessage = Field(..., description="Assistant response")
    session_id: str = Field(..., description="Session ID")

    # Context used
    context_chunks_used: int = Field(default=0)
    total_tokens_used: int = Field(default=0)

    # Processing info
    processing_time_ms: float = Field(default=0)


class SearchRequest(BaseModel):
    """Request to search the knowledge base."""

    query: str = Field(..., description="Search query", min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)
    module_filter: Optional[str] = Field(None)
    min_score: float = Field(default=0.5, ge=0, le=1)


class SearchResult(BaseModel):
    """A single search result."""

    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: Dict


class SearchResponse(BaseModel):
    """Response from search endpoint."""

    results: List[SearchResult]
    query: str
    total_results: int
    processing_time_ms: float


class VoiceCommandRequest(BaseModel):
    """Request to process voice command (Whisper integration)."""

    audio_base64: str = Field(..., description="Base64 encoded audio")
    language: str = Field(default="en", description="Language code")


class VoiceCommandResponse(BaseModel):
    """Response from voice command processing."""

    transcript: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., description="Transcription confidence")
    chat_response: Optional[ChatResponse] = Field(None, description="Chat response if requested")
