"""
SQLAlchemy models for the RAG chatbot database.
Stores documents, chunks, embeddings metadata, and chat history.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Document(Base):
    """
    Represents a source document (MDX file) from the book.
    Each document can have multiple chunks.
    """
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    file_path: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    chapter: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    chunks: Mapped[List["Chunk"]] = relationship(
        "Chunk", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_documents_module", "module"),
        Index("idx_documents_chapter", "chapter"),
        Index("idx_documents_active", "is_active"),
    )


class Chunk(Base):
    """
    Represents a semantic chunk of a document.
    Chunks are embedded and stored in Qdrant for similarity search.
    """
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    section_heading: Mapped[Optional[str]] = mapped_column(String(500))
    chunk_type: Mapped[str] = mapped_column(
        String(50), default="text"
    )  # text, code, table, list
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Embedding info (stored in Qdrant, reference here)
    qdrant_point_id: Mapped[Optional[str]] = mapped_column(String(100))
    embedding_model: Mapped[str] = mapped_column(String(100), default="embed-english-v3.0")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_embedded: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("idx_chunks_document", "document_id"),
        Index("idx_chunks_embedded", "is_embedded"),
        Index("idx_chunks_type", "chunk_type"),
    )


class ChatSession(Base):
    """
    Represents a chat session with a user.
    Sessions track conversation history and mode.
    """
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[str]] = mapped_column(String(100))  # Optional user tracking
    mode: Mapped[str] = mapped_column(
        String(50), default="book"
    )  # book, selection_only
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Relationships
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_sessions_user", "user_id"),
        Index("idx_sessions_active", "is_active"),
        Index("idx_sessions_created", "created_at"),
    )


class ChatMessage(Base):
    """
    Represents a single message in a chat session.
    Stores both user questions and assistant responses.
    """
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # For selection-only mode
    selected_text: Mapped[Optional[str]] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String(50), default="book")

    # RAG metadata
    retrieved_chunks: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    citations: Mapped[Optional[dict]] = mapped_column(JSON)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)

    # Processing info
    processing_time_ms: Mapped[Optional[int]] = mapped_column(Integer)
    token_count: Mapped[Optional[int]] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Relationships
    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")

    __table_args__ = (
        Index("idx_messages_session", "session_id"),
        Index("idx_messages_role", "role"),
        Index("idx_messages_created", "created_at"),
    )


# SQL Schema for manual creation (Neon)
SCHEMA_SQL = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path VARCHAR(500) UNIQUE NOT NULL,
    module VARCHAR(100) NOT NULL,
    chapter VARCHAR(200) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_documents_module ON documents(module);
CREATE INDEX IF NOT EXISTS idx_documents_chapter ON documents(chapter);
CREATE INDEX IF NOT EXISTS idx_documents_active ON documents(is_active);

-- Chunks table
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    section_heading VARCHAR(500),
    chunk_type VARCHAR(50) DEFAULT 'text',
    token_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    qdrant_point_id VARCHAR(100),
    embedding_model VARCHAR(100) DEFAULT 'embed-english-v3.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_embedded BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedded ON chunks(is_embedded);
CREATE INDEX IF NOT EXISTS idx_chunks_type ON chunks(chunk_type);

-- Chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100),
    mode VARCHAR(50) DEFAULT 'book',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON chat_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_created ON chat_sessions(created_at);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    selected_text TEXT,
    mode VARCHAR(50) DEFAULT 'book',
    retrieved_chunks TEXT[],
    citations JSONB,
    confidence_score FLOAT,
    processing_time_ms INTEGER,
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_role ON chat_messages(role);
CREATE INDEX IF NOT EXISTS idx_messages_created ON chat_messages(created_at);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""
