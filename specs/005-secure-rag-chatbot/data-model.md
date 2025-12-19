# Data Model: Secure Dynamic RAG Chatbot

**Feature Branch**: `005-secure-rag-chatbot`
**Created**: 2025-12-18
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

This document defines the data structures for the Secure Dynamic RAG Chatbot system.

## Core Entities

### 1. ChatMessage

Represents a single message in a conversation.

```python
class ChatMessage(BaseModel):
    """A single message in the conversation."""
    id: str                          # UUID
    session_id: str                  # Reference to ChatSession
    role: Literal["user", "assistant"]
    content: str                     # Message text
    mode: ChatMode                   # book | selection
    citations: list[Citation] | None # Only for assistant messages in book mode
    created_at: datetime
```

**Storage**: Neon Postgres `chat_messages` table

### 2. Citation

Reference to source content from the book.

```python
class Citation(BaseModel):
    """Reference to book content."""
    module: str                      # e.g., "Module 1: ROS 2"
    chapter: str                     # e.g., "Chapter 3: Topics"
    section: str | None              # e.g., "Publisher Nodes"
    relevance_score: float           # 0.0 - 1.0
    content_snippet: str             # First 200 chars of matched content
```

**Storage**: Embedded in ChatMessage (JSON column)

### 3. ChatSession

A conversation session containing multiple messages.

```python
class ChatSession(BaseModel):
    """A conversation session."""
    id: str                          # UUID
    created_at: datetime
    updated_at: datetime
    active_mode: ChatMode            # Current mode: book | selection
    module_filter: str | None        # Optional module filter
    message_count: int               # Number of messages
```

**Storage**: Neon Postgres `chat_sessions` table

### 4. BookChunk

A chunk of book content stored in the vector database.

```python
class BookChunk(BaseModel):
    """A chunk of book content for RAG retrieval."""
    id: str                          # UUID
    module: str                      # Module name
    chapter: str                     # Chapter name
    section: str | None              # Section name
    content: str                     # Chunk text (500-1000 tokens)
    embedding: list[float]           # 1024-dim Cohere vector
    metadata: dict                   # Additional metadata
    created_at: datetime
```

**Storage**: Qdrant `book_chunks` collection

### 5. ChatMode (Enum)

Defines the two operating modes.

```python
class ChatMode(str, Enum):
    """Chat operating mode."""
    BOOK = "book"           # RAG mode: queries Qdrant
    SELECTION = "selection" # Selection-only: uses highlighted text only
```

## Database Schemas

### Neon Postgres

```sql
-- Chat sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    active_mode VARCHAR(20) DEFAULT 'book',
    module_filter VARCHAR(100),
    message_count INTEGER DEFAULT 0
);

-- Chat messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    mode VARCHAR(20) NOT NULL,
    citations JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_messages_session ON chat_messages(session_id);
CREATE INDEX idx_messages_created ON chat_messages(created_at);
CREATE INDEX idx_sessions_updated ON chat_sessions(updated_at);
```

### Qdrant Collection

```python
# Collection configuration
collection_config = {
    "name": "book_chunks",
    "vectors_config": {
        "size": 1024,           # Cohere embed-english-v3.0
        "distance": "Cosine"
    }
}

# Payload schema
payload_schema = {
    "module": "keyword",        # Filterable
    "chapter": "keyword",       # Filterable
    "section": "keyword",       # Filterable
    "content": "text",          # Full text
    "created_at": "datetime"
}
```

## API Request/Response Models

### Query Request

```python
class QueryRequest(BaseModel):
    """RAG query request."""
    query: str                       # User's question
    mode: ChatMode                   # book | selection
    selected_text: str | None = None # Required if mode=selection
    session_id: str | None = None    # Optional session tracking
    module_filter: str | None = None # Optional module filter

    @model_validator(mode='after')
    def validate_selection_mode(self):
        if self.mode == ChatMode.SELECTION and not self.selected_text:
            raise ValueError("selected_text required for selection mode")
        return self
```

### Query Response

```python
class QueryResponse(BaseModel):
    """RAG query response."""
    answer: str                      # Generated response
    citations: list[Citation] | None # Sources (book mode only)
    mode: ChatMode                   # Mode used
    session_id: str                  # Session ID
    processing_time_ms: int          # Performance metric
```

### Health Response

```python
class HealthResponse(BaseModel):
    """Health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    services: dict[str, bool]        # Service availability
    timestamp: datetime
```

## Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│   Qdrant    │
│  (React)    │     │  (FastAPI)  │     │  (Vectors)  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    Neon     │
                    │  (Sessions) │
                    └─────────────┘

Book Mode Flow:
1. User sends query → Backend
2. Backend embeds query → Cohere
3. Backend searches → Qdrant
4. Backend generates → OpenAI
5. Backend stores → Neon
6. Response → Frontend

Selection Mode Flow:
1. User sends query + selected_text → Backend
2. Backend generates → OpenAI (using selected_text as context)
3. Backend stores → Neon
4. Response → Frontend
(NO Qdrant interaction in selection mode)
```

## Validation Rules

| Field | Rule | Error Message |
|-------|------|---------------|
| query | 1-2000 chars | "Query must be 1-2000 characters" |
| selected_text | Required if mode=selection | "Selected text required for selection mode" |
| selected_text | Max 5000 chars | "Selected text too long (max 5000 chars)" |
| module_filter | Valid module name | "Invalid module filter" |
| session_id | Valid UUID | "Invalid session ID format" |

## Security Considerations

1. **No PII Storage**: Chat content may contain user questions but no authentication data
2. **Session Isolation**: Sessions are isolated by UUID, no cross-session access
3. **Input Sanitization**: All user input is sanitized before storage
4. **Citation Integrity**: Citations are generated server-side, not user-provided
