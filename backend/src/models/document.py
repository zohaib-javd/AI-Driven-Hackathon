"""
Document models for the RAG system.
Defines schemas for documents, chunks, and embeddings.
"""

from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Types of documents in the book."""
    CHAPTER = "chapter"
    GLOSSARY = "glossary"
    CODE_EXAMPLE = "code_example"
    EXERCISE = "exercise"


class ChunkMetadata(BaseModel):
    """Metadata associated with a document chunk."""

    document_id: str = Field(..., description="Unique document identifier")
    module: str = Field(..., description="Module name (e.g., 'module-1-ros2')")
    chapter: str = Field(..., description="Chapter slug")
    chapter_title: str = Field(..., description="Human-readable chapter title")
    section: Optional[str] = Field(None, description="Section within chapter")
    document_type: DocumentType = Field(default=DocumentType.CHAPTER)

    # Position info
    chunk_index: int = Field(..., description="Index of chunk within document")
    total_chunks: int = Field(..., description="Total chunks in document")

    # Content hints
    has_code: bool = Field(default=False, description="Contains code blocks")
    has_diagram: bool = Field(default=False, description="Contains Mermaid diagrams")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentChunk(BaseModel):
    """A chunk of document content with metadata."""

    id: str = Field(..., description="Unique chunk identifier")
    content: str = Field(..., description="Text content of the chunk")
    metadata: ChunkMetadata = Field(..., description="Chunk metadata")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")

    # Token count for context management
    token_count: int = Field(default=0, description="Number of tokens in content")


class Document(BaseModel):
    """A complete document (chapter) from the book."""

    id: str = Field(..., description="Unique document identifier")
    path: str = Field(..., description="File path relative to docs folder")
    title: str = Field(..., description="Document title")
    description: Optional[str] = Field(None, description="Document description")

    # Content
    raw_content: str = Field(..., description="Raw MDX content")
    frontmatter: Dict = Field(default_factory=dict, description="YAML frontmatter")

    # Chunks
    chunks: List[DocumentChunk] = Field(default_factory=list)

    # Metadata
    module: str = Field(..., description="Module name")
    sidebar_position: int = Field(default=0)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EmbeddingRequest(BaseModel):
    """Request to generate embeddings for text."""

    texts: List[str] = Field(..., description="Texts to embed")
    model: str = Field(default="text-embedding-3-large")


class EmbeddingResponse(BaseModel):
    """Response containing generated embeddings."""

    embeddings: List[List[float]] = Field(..., description="Vector embeddings")
    model: str = Field(..., description="Model used")
    usage: Dict = Field(default_factory=dict, description="Token usage")
