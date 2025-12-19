# Research: Secure Dynamic RAG Chatbot

**Feature Branch**: `005-secure-rag-chatbot`
**Created**: 2025-12-18
**Status**: Complete
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Research Questions

### RQ-001: Secure Credential Handling in FastAPI

**Question**: What is the best practice for fail-fast credential validation in FastAPI with Pydantic?

**Finding**: Use Pydantic `BaseSettings` with `@lru_cache` and FastAPI lifespan events.

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    cohere_api_key: str
    openai_api_key: str
    qdrant_url: str
    qdrant_api_key: str
    neon_database_url: str

    model_config = SettingsConfigDict(env_file=".env")

@lru_cache
def get_settings() -> Settings:
    """Fail-fast: raises ValidationError if any required field is missing."""
    return Settings()

# In main.py lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate all secrets on startup - fails immediately if missing
    settings = get_settings()
    yield
```

**Source**: Pydantic Settings documentation, FastAPI best practices
**Decision**: Adopt this pattern for `backend/src/config.py`

---

### RQ-002: Cohere Embedding Integration

**Question**: How to integrate Cohere embed-english-v3.0 with Qdrant vector store?

**Finding**: Cohere v3 embeddings require `input_type` parameter for optimal performance.

```python
import cohere

co = cohere.Client(api_key=settings.cohere_api_key)

# For documents being indexed
doc_embeddings = co.embed(
    texts=chunks,
    model="embed-english-v3.0",
    input_type="search_document"
).embeddings

# For queries
query_embedding = co.embed(
    texts=[query],
    model="embed-english-v3.0",
    input_type="search_query"
).embeddings[0]
```

**Key Details**:
- Model: `embed-english-v3.0`
- Dimensions: 1024
- `input_type="search_document"` for indexing
- `input_type="search_query"` for retrieval
- Rate limits: 100 calls/minute (free tier), 10,000 calls/minute (production)

**Source**: Cohere API documentation
**Decision**: Implement in `backend/src/services/embeddings.py`

---

### RQ-003: Qdrant Cloud Setup

**Question**: How to configure Qdrant Cloud client with secure authentication?

**Finding**: Qdrant Cloud requires URL and API key, supports async client.

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key,
)

# Create collection with Cohere dimensions
client.create_collection(
    collection_name="book_chunks",
    vectors_config=VectorParams(
        size=1024,  # Cohere embed-english-v3.0
        distance=Distance.COSINE
    )
)
```

**Key Details**:
- Collection name: `book_chunks`
- Vector size: 1024 (Cohere v3)
- Distance metric: Cosine similarity
- Payload: `{module, chapter, section, content, metadata}`

**Source**: Qdrant documentation
**Decision**: Implement in `backend/src/services/vectorstore.py`

---

### RQ-004: Selection-Only Mode Isolation

**Question**: How to strictly enforce that selection-only mode never queries Qdrant?

**Finding**: Use explicit mode parameter with backend validation and separate code paths.

```python
from enum import Enum

class ChatMode(str, Enum):
    BOOK = "book"
    SELECTION = "selection"

async def process_query(
    query: str,
    mode: ChatMode,
    selected_text: str | None = None
) -> str:
    if mode == ChatMode.SELECTION:
        # CRITICAL: Never touch Qdrant in this path
        if not selected_text:
            raise ValueError("Selection mode requires selected_text")
        context = selected_text
    else:
        # Book mode: Query Qdrant
        context = await retrieve_from_qdrant(query)

    return await generate_response(query, context)
```

**Isolation Guarantees**:
1. Mode is explicit parameter, not inferred
2. Selection path has zero Qdrant imports/calls
3. Backend logs mode for audit
4. Tests verify isolation with mock assertions

**Source**: Security best practices
**Decision**: Implement strict mode branching in `backend/src/services/rag.py`

---

### RQ-005: React Text Selection Detection

**Question**: How to detect text selection in Docusaurus/React and pass to chatbot?

**Finding**: Use `window.getSelection()` API with debounced event listener.

```typescript
import { useState, useEffect, useCallback } from 'react';

function useTextSelection() {
  const [selectedText, setSelectedText] = useState<string>('');

  const handleSelectionChange = useCallback(() => {
    const selection = window.getSelection();
    const text = selection?.toString().trim() || '';
    setSelectedText(text);
  }, []);

  useEffect(() => {
    document.addEventListener('selectionchange', handleSelectionChange);
    return () => {
      document.removeEventListener('selectionchange', handleSelectionChange);
    };
  }, [handleSelectionChange]);

  return selectedText;
}
```

**Key Details**:
- Event: `selectionchange` on document
- Minimum selection: 10 characters for meaningful context
- Maximum selection: 5000 characters to stay within LLM context limits
- Clear selection when switching modes

**Source**: MDN Web Docs, React patterns
**Decision**: Implement in `RAGChatWidget` component

---

### RQ-006: OpenAI Response Generation with Grounding

**Question**: How to generate grounded responses that cite sources?

**Finding**: Use system prompt with strict grounding instructions.

```python
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
```

**Key Details**:
- Model: `gpt-4-turbo-preview` for quality
- Temperature: 0.3 for consistency
- Max tokens: 1000 for responses
- Include citations in response format

**Source**: OpenAI best practices
**Decision**: Implement in `backend/src/services/rag.py`

---

### RQ-007: Frontend Secret Isolation Verification

**Question**: How to verify frontend bundle contains zero secrets?

**Finding**: Use build-time checks and bundle analysis.

```bash
# Check for leaked secrets in build output
grep -r "sk-" ./build/ && echo "FAIL: OpenAI key leaked" && exit 1
grep -r "cohere" ./build/ | grep -i "key\|api\|secret" && echo "FAIL: Cohere key leaked" && exit 1

# Use environment variable for API endpoint only
REACT_APP_API_URL=https://api.example.com
```

**Verification Checklist**:
- [ ] No `process.env` containing API keys in frontend
- [ ] All external calls go to `/api/*` endpoints
- [ ] Network tab shows no direct calls to Cohere/OpenAI/Qdrant
- [ ] Bundle size check (secrets would be visible strings)

**Source**: Security best practices
**Decision**: Add verification script to CI/CD

---

## Technology Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Embeddings | Cohere embed-english-v3.0 | Constitution mandate, 1024 dim, good semantic quality |
| Vector DB | Qdrant Cloud | Constitution mandate, managed service, async support |
| LLM | OpenAI gpt-4-turbo | Constitution mandate, best quality for grounded responses |
| Metadata DB | Neon Serverless Postgres | Constitution mandate, serverless, async support |
| Backend | FastAPI + Pydantic | Constitution mandate, async, validation |
| Frontend | Docusaurus + React | Constitution mandate, existing infrastructure |

## Open Questions (Resolved)

All research questions have been resolved. No NEEDS CLARIFICATION items remain.

## References

1. [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
2. [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
3. [Cohere Embed v3 Documentation](https://docs.cohere.com/reference/embed)
4. [Qdrant Python Client](https://qdrant.tech/documentation/quick-start/)
5. [OpenAI Chat Completions](https://platform.openai.com/docs/guides/text-generation)
6. [MDN Selection API](https://developer.mozilla.org/en-US/docs/Web/API/Selection)
