# Implementation Plan: Secure Dynamic RAG Chatbot

**Branch**: `005-secure-rag-chatbot` | **Date**: 2025-12-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-secure-rag-chatbot/spec.md`
**Constitution Version**: 2.0.0

## Summary

Build a secure, dynamic RAG chatbot for the Physical AI & Humanoid Robotics book platform. The chatbot provides context-aware answers grounded in book content (Book Mode) or user-selected text only (Selection-Only Mode), while enforcing strict security boundaries with zero hardcoded secrets, fail-fast credential validation, and complete frontend isolation from API credentials.

**Key Technical Approach**:
- FastAPI backend with Pydantic settings for environment variable validation
- Cohere embeddings (embed-english-v3.0, 1024 dimensions) for semantic search
- Qdrant Cloud for vector storage and retrieval
- OpenAI GPT-4 for response generation with grounding
- React chatbot widget with text selection detection
- Strict mode isolation: Selection-Only NEVER queries Qdrant

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript (frontend)
**Primary Dependencies**: FastAPI, Pydantic, cohere, openai, qdrant-client, React, Docusaurus
**Storage**: Qdrant Cloud (vectors), Neon Serverless Postgres (metadata/sessions)
**Testing**: pytest (backend), manual verification (frontend)
**Target Platform**: Linux server (backend), Web browsers (frontend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: <5s p95 response time, support 100 concurrent users
**Constraints**: Zero secrets in frontend, fail-fast on missing credentials
**Scale/Scope**: ~50 chapters of book content, ~10k daily queries expected

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Status | Implementation |
|-----------|-------------|--------|----------------|
| **P1: Security-First** | Architecture enforces trusted/untrusted separation | ✅ PASS | Backend-only API access; frontend calls `/api/rag/*` |
| **P2: Zero Hardcoded Secrets** | All secrets via environment variables | ✅ PASS | Pydantic Settings with `env_file=".env"` |
| **P3: Grounded Responses** | AI answers from book/selection only | ✅ PASS | RAG retrieval required; no freeform generation |
| **P4: Deterministic Retrieval** | Selection-only mode isolated | ✅ PASS | Explicit `mode` parameter; backend enforces |
| **P5: Trust Boundaries** | Frontend has zero secrets | ✅ PASS | No API keys in frontend bundle |

| Security Standard | Requirement | Status | Implementation |
|-------------------|-------------|--------|----------------|
| **S1: Env Var Only** | Secrets from env vars | ✅ PASS | `Settings` class with empty defaults |
| **S2: Fail-Fast** | Exit on missing secrets | ✅ PASS | Startup validation with `@lru_cache` |
| **S3: Frontend Isolation** | No direct external API calls | ✅ PASS | All calls proxied through backend |
| **S4: Backend Validation** | Validate before accepting requests | ✅ PASS | Lifespan event validates secrets |
| **S5: Selection Isolation** | No Qdrant in selection mode | ✅ PASS | Mode check before retrieval |

**All gates passed. Proceeding to Phase 0.**

## Project Structure

### Documentation (this feature)

```text
specs/005-secure-rag-chatbot/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── rag-api.yaml     # OpenAPI spec
└── checklists/
    └── requirements.md  # Validation checklist
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py          # Existing chat endpoints
│   │   └── rag.py           # RAG-specific endpoints (enhanced)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py      # Async database connection
│   │   └── models.py        # SQLAlchemy models
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── loader.py        # MDX document loader
│   │   ├── chunker.py       # Semantic chunking
│   │   └── pipeline.py      # Ingestion orchestration
│   ├── services/
│   │   ├── __init__.py
│   │   ├── embeddings.py    # Cohere embedding service
│   │   ├── vectorstore.py   # Qdrant operations
│   │   └── rag.py           # RAG query service
│   ├── config.py            # Pydantic Settings (secrets validation)
│   └── main.py              # FastAPI app with lifespan
├── tests/
│   ├── test_security.py     # Secret isolation tests
│   ├── test_rag.py          # RAG functionality tests
│   └── test_modes.py        # Mode isolation tests
├── .env.example             # Documented env vars (no values)
├── requirements.txt
└── Dockerfile

physical-ai-humanoid-robotics/
├── src/
│   ├── components/
│   │   └── RAGChatWidget/
│   │       ├── index.tsx    # Main chatbot component
│   │       └── styles.module.css
│   └── theme/
│       └── Root.tsx         # Includes chatbot globally
├── docusaurus.config.ts
└── package.json
```

**Structure Decision**: Web application with separate backend (FastAPI) and frontend (Docusaurus/React). Backend holds all secrets and external API access. Frontend is completely stateless regarding credentials.

## Related Artifacts

- [research.md](./research.md) - Technology research and decisions
- [data-model.md](./data-model.md) - Entity definitions and schemas
- [quickstart.md](./quickstart.md) - Developer setup guide
- [contracts/rag-api.yaml](./contracts/rag-api.yaml) - OpenAPI specification

---

## Phase 1: Security Foundation

**Objective**: Establish secure credential handling before any external API integration.

### Tasks

#### 1.1 Create `.env.example`

**File**: `backend/.env.example`

```env
# Required - Cohere Embeddings
COHERE_API_KEY=

# Required - OpenAI Chat
OPENAI_API_KEY=

# Required - Qdrant Vector Database
QDRANT_URL=
QDRANT_API_KEY=

# Required - Neon Postgres Database
NEON_DATABASE_URL=

# Optional - Configuration
COLLECTION_NAME=book_chunks
EMBEDDING_MODEL=embed-english-v3.0
CHAT_MODEL=gpt-4-turbo-preview
```

#### 1.2 Implement Pydantic Settings

**File**: `backend/src/config.py`

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings with fail-fast validation."""

    # Required credentials
    cohere_api_key: str
    openai_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    neon_database_url: str

    # Optional configuration
    collection_name: str = "book_chunks"
    embedding_model: str = "embed-english-v3.0"
    chat_model: str = "gpt-4-turbo-preview"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

@lru_cache
def get_settings() -> Settings:
    """Get cached settings. Raises ValidationError if credentials missing."""
    return Settings()
```

#### 1.3 Add Lifespan Validation

**File**: `backend/src/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .config import get_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate all credentials on startup
    try:
        settings = get_settings()
        print("All credentials validated successfully")
    except Exception as e:
        print(f"ERROR: {e}")
        raise SystemExit(1)
    yield

app = FastAPI(lifespan=lifespan)
```

#### 1.4 Update `.gitignore`

```gitignore
# Secrets
.env
*.env
.env.local
.env.*.local

# Never commit
**/secrets/
**/*.pem
**/*.key
```

### Acceptance Criteria

- [ ] Backend refuses to start with missing `COHERE_API_KEY`
- [ ] Backend refuses to start with missing `OPENAI_API_KEY`
- [ ] Backend refuses to start with missing `QDRANT_URL`
- [ ] Backend refuses to start with missing `QDRANT_API_KEY`
- [ ] Backend refuses to start with missing `NEON_DATABASE_URL`
- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` has all variables documented with empty values

---

## Phase 2: Backend Services

**Objective**: Implement core RAG services with secure credential access.

### Tasks

#### 2.1 Cohere Embedding Service

**File**: `backend/src/services/embeddings.py`

```python
import cohere
from ..config import get_settings

class CohereEmbeddingService:
    def __init__(self):
        settings = get_settings()
        self.client = cohere.Client(api_key=settings.cohere_api_key)
        self.model = settings.embedding_model

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embed(
            texts=texts,
            model=self.model,
            input_type="search_document"
        )
        return response.embeddings

    async def embed_query(self, query: str) -> list[float]:
        response = self.client.embed(
            texts=[query],
            model=self.model,
            input_type="search_query"
        )
        return response.embeddings[0]
```

#### 2.2 Qdrant Vector Store

**File**: `backend/src/services/vectorstore.py`

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from ..config import get_settings

class QdrantVectorStore:
    def __init__(self):
        settings = get_settings()
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )
        self.collection_name = settings.collection_name

    async def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        module_filter: str | None = None
    ) -> list[dict]:
        filter_conditions = None
        if module_filter:
            filter_conditions = {"must": [{"key": "module", "match": {"value": module_filter}}]}

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter_conditions
        )
        return [{"payload": r.payload, "score": r.score} for r in results]
```

#### 2.3 RAG Query Service

**File**: `backend/src/services/rag.py`

```python
from enum import Enum
from openai import OpenAI
from ..config import get_settings
from .embeddings import CohereEmbeddingService
from .vectorstore import QdrantVectorStore

class ChatMode(str, Enum):
    BOOK = "book"
    SELECTION = "selection"

SYSTEM_PROMPT = """You are a helpful assistant for the Physical AI & Humanoid Robotics book.
Answer questions using ONLY the provided context. If the context doesn't contain
relevant information, say "I couldn't find relevant information in the book."

RULES:
1. Only use information from the provided context
2. Cite sources using [Module X, Chapter Y] format
3. Never make up information not in the context
4. Be concise and technically accurate

Context:
{context}
"""

class RAGService:
    def __init__(self):
        settings = get_settings()
        self.openai = OpenAI(api_key=settings.openai_api_key)
        self.embeddings = CohereEmbeddingService()
        self.vectorstore = QdrantVectorStore()
        self.chat_model = settings.chat_model

    async def query(
        self,
        query: str,
        mode: ChatMode,
        selected_text: str | None = None,
        module_filter: str | None = None
    ) -> dict:
        if mode == ChatMode.SELECTION:
            # CRITICAL: Never touch Qdrant in selection mode
            if not selected_text:
                raise ValueError("selected_text required for selection mode")
            context = selected_text
            citations = None
        else:
            # Book mode: Query Qdrant
            query_vector = await self.embeddings.embed_query(query)
            results = await self.vectorstore.search(
                query_vector,
                module_filter=module_filter
            )
            context = self._format_context(results)
            citations = self._extract_citations(results)

        answer = await self._generate_response(query, context)
        return {"answer": answer, "citations": citations, "mode": mode}

    def _format_context(self, results: list[dict]) -> str:
        return "\n\n".join([
            f"[{r['payload']['module']}, {r['payload']['chapter']}]\n{r['payload']['content']}"
            for r in results
        ])

    def _extract_citations(self, results: list[dict]) -> list[dict]:
        return [
            {
                "module": r["payload"]["module"],
                "chapter": r["payload"]["chapter"],
                "section": r["payload"].get("section"),
                "relevance_score": r["score"],
                "content_snippet": r["payload"]["content"][:200]
            }
            for r in results
        ]

    async def _generate_response(self, query: str, context: str) -> str:
        response = self.openai.chat.completions.create(
            model=self.chat_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
                {"role": "user", "content": query}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        return response.choices[0].message.content
```

#### 2.4 RAG API Endpoints

**File**: `backend/src/api/rag.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator
from ..services.rag import RAGService, ChatMode
import time

router = APIRouter(prefix="/api/rag", tags=["RAG"])

class QueryRequest(BaseModel):
    query: str
    mode: ChatMode
    selected_text: str | None = None
    session_id: str | None = None
    module_filter: str | None = None

    @model_validator(mode='after')
    def validate_selection_mode(self):
        if self.mode == ChatMode.SELECTION and not self.selected_text:
            raise ValueError("selected_text required for selection mode")
        if self.selected_text and len(self.selected_text) > 5000:
            raise ValueError("selected_text too long (max 5000 chars)")
        return self

class QueryResponse(BaseModel):
    answer: str
    citations: list[dict] | None
    mode: ChatMode
    session_id: str
    processing_time_ms: int

@router.post("/query", response_model=QueryResponse)
async def rag_query(request: QueryRequest):
    start = time.time()
    service = RAGService()

    try:
        result = await service.query(
            query=request.query,
            mode=request.mode,
            selected_text=request.selected_text,
            module_filter=request.module_filter
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Service temporarily busy")

    processing_time = int((time.time() - start) * 1000)

    return QueryResponse(
        answer=result["answer"],
        citations=result["citations"],
        mode=result["mode"],
        session_id=request.session_id or "new-session",
        processing_time_ms=processing_time
    )

@router.get("/health")
async def health_check():
    # Check all services
    return {
        "status": "healthy",
        "services": {
            "qdrant": True,
            "openai": True,
            "cohere": True,
            "database": True
        }
    }
```

### Acceptance Criteria

- [ ] Cohere embeddings work with embed-english-v3.0
- [ ] Qdrant search returns relevant chunks
- [ ] OpenAI generates grounded responses
- [ ] `/api/rag/query` endpoint accepts mode parameter
- [ ] `/api/rag/health` endpoint returns service status

---

## Phase 3: Frontend Widget

**Objective**: Build React chatbot with text selection support.

### Tasks

#### 3.1 RAG Chat Widget Component

**File**: `physical-ai-humanoid-robotics/src/components/RAGChatWidget/index.tsx`

```typescript
import React, { useState, useEffect, useCallback } from 'react';
import styles from './styles.module.css';

type ChatMode = 'book' | 'selection';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  mode: ChatMode;
}

function useTextSelection() {
  const [selectedText, setSelectedText] = useState('');

  const handleSelectionChange = useCallback(() => {
    const selection = window.getSelection();
    const text = selection?.toString().trim() || '';
    if (text.length >= 10 && text.length <= 5000) {
      setSelectedText(text);
    }
  }, []);

  useEffect(() => {
    document.addEventListener('selectionchange', handleSelectionChange);
    return () => document.removeEventListener('selectionchange', handleSelectionChange);
  }, [handleSelectionChange]);

  return { selectedText, clearSelection: () => setSelectedText('') };
}

export default function RAGChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState<ChatMode>('book');
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const { selectedText, clearSelection } = useTextSelection();

  const sendMessage = async () => {
    if (!input.trim()) return;
    if (mode === 'selection' && !selectedText) {
      alert('Please select some text first');
      return;
    }

    const userMessage: Message = { role: 'user', content: input, mode };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: input,
          mode,
          selected_text: mode === 'selection' ? selectedText : undefined
        })
      });

      const data = await response.json();
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer,
        mode
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Service temporarily busy, please try again.',
        mode
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.widget}>
      {!isOpen ? (
        <button onClick={() => setIsOpen(true)} className={styles.trigger}>
          💬
        </button>
      ) : (
        <div className={styles.container}>
          <div className={styles.header}>
            <span>Book Assistant</span>
            <button onClick={() => setIsOpen(false)}>×</button>
          </div>

          <div className={styles.modeSelector}>
            <button
              className={mode === 'book' ? styles.active : ''}
              onClick={() => { setMode('book'); clearSelection(); }}
            >
              📚 Book Mode
            </button>
            <button
              className={mode === 'selection' ? styles.active : ''}
              onClick={() => setMode('selection')}
            >
              ✂️ Selection Mode
            </button>
          </div>

          {mode === 'selection' && selectedText && (
            <div className={styles.selectionPreview}>
              Selected: "{selectedText.slice(0, 50)}..."
            </div>
          )}

          <div className={styles.messages}>
            {messages.map((msg, i) => (
              <div key={i} className={styles[msg.role]}>
                {msg.content}
              </div>
            ))}
            {loading && <div className={styles.loading}>Thinking...</div>}
          </div>

          <div className={styles.inputArea}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyPress={e => e.key === 'Enter' && sendMessage()}
              placeholder={mode === 'selection' ? 'Ask about selection...' : 'Ask about the book...'}
            />
            <button onClick={sendMessage} disabled={loading}>
              Send
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

### Acceptance Criteria

- [ ] Chat widget appears on all book pages
- [ ] Mode selector switches between Book and Selection
- [ ] Text selection is detected and displayed
- [ ] Messages are sent to `/api/rag/query` (no direct external calls)
- [ ] Loading indicator shows during requests
- [ ] Error messages are user-friendly

---

## Phase 4: Guardrails

**Objective**: Enforce security boundaries and input validation.

### Tasks

#### 4.1 Mode Isolation Test

**File**: `backend/tests/test_modes.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from src.services.rag import RAGService, ChatMode

@pytest.mark.asyncio
async def test_selection_mode_never_queries_qdrant():
    """CRITICAL: Selection mode MUST NOT touch Qdrant."""
    service = RAGService()

    with patch.object(service.vectorstore, 'search') as mock_search:
        await service.query(
            query="Explain this",
            mode=ChatMode.SELECTION,
            selected_text="ROS 2 uses DDS"
        )

        # Assert Qdrant was NEVER called
        mock_search.assert_not_called()

@pytest.mark.asyncio
async def test_book_mode_queries_qdrant():
    """Book mode MUST query Qdrant."""
    service = RAGService()

    with patch.object(service.vectorstore, 'search') as mock_search:
        mock_search.return_value = []
        await service.query(
            query="What is URDF?",
            mode=ChatMode.BOOK
        )

        # Assert Qdrant was called
        mock_search.assert_called_once()
```

#### 4.2 Input Validation

```python
# In QueryRequest model
@model_validator(mode='after')
def validate_inputs(self):
    # Query length
    if len(self.query) > 2000:
        raise ValueError("Query too long (max 2000 chars)")

    # Selection requirements
    if self.mode == ChatMode.SELECTION:
        if not self.selected_text:
            raise ValueError("selected_text required for selection mode")
        if len(self.selected_text) < 10:
            raise ValueError("selected_text too short (min 10 chars)")
        if len(self.selected_text) > 5000:
            raise ValueError("selected_text too long (max 5000 chars)")

    return self
```

#### 4.3 Error Sanitization

```python
# Never expose internal errors
@router.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    # Log full error internally
    logger.error(f"Internal error: {exc}")

    # Return sanitized message
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "Service temporarily busy, please try again."}
    )
```

### Acceptance Criteria

- [ ] Selection mode test verifies zero Qdrant calls
- [ ] Book mode test verifies Qdrant is called
- [ ] Input validation rejects invalid queries
- [ ] Error messages never expose internal details

---

## Phase 5: Deployment

**Objective**: Secure deployment with environment variable injection.

### Tasks

#### 5.1 Dockerfile

**File**: `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# No secrets in image - injected at runtime
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 5.2 CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

#### 5.3 Health Check Endpoint

```python
@router.get("/health")
async def health_check():
    status = "healthy"
    services = {}

    # Check Qdrant
    try:
        vectorstore = QdrantVectorStore()
        vectorstore.client.get_collections()
        services["qdrant"] = True
    except:
        services["qdrant"] = False
        status = "degraded"

    # Similar checks for other services...

    return {"status": status, "services": services}
```

### Acceptance Criteria

- [ ] Docker image builds without secrets
- [ ] Container starts with environment variables
- [ ] CORS configured for frontend domain only
- [ ] Health endpoint checks all dependencies

---

## Risk Analysis

| Risk | Mitigation |
|------|------------|
| Secret leakage in logs | Never log credential values; use structured logging |
| Selection mode queries Qdrant | Explicit mode check; comprehensive tests |
| Rate limit exceeded | Implement retry with backoff; display user message |
| Frontend bundle contains secrets | Build-time verification script; CI check |

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Startup with missing creds | 100% fail | Manual test |
| Selection mode isolation | 100% no Qdrant | Unit tests |
| Frontend secret scan | 0 secrets | Automated scan |
| Response time p95 | <5s | Load testing |
| Citation accuracy | >90% | Manual review |
