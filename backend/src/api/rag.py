"""
RAG API endpoints for the Physical AI RAG Chatbot.

SECURITY FEATURES:
- Strict mode isolation (selection mode NEVER queries Qdrant)
- Input validation with clear error messages
- Sanitized error responses
- No credential exposure in responses

MODES:
1. Book Mode (/query) - Full RAG with Qdrant vector search
2. Selection-Only Mode (/query-selection) - Uses ONLY provided text
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
import logging
import json
from datetime import datetime
from enum import Enum

from ..services.rag import get_rag_service, RAGResponse, Citation
from ..services.embeddings import get_embedding_service
from ..ingestion import IngestionPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["RAG"])


# =============================================================================
# Request/Response Models with Validation
# =============================================================================

class ChatMode(str, Enum):
    """Available chat modes."""
    BOOK = "book"
    SELECTION = "selection_only"


class RAGQueryRequest(BaseModel):
    """Request for standard RAG query (Book Mode)."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question (1-2000 characters)"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of chunks to retrieve (1-20)"
    )
    module_filter: Optional[str] = Field(
        default=None,
        description="Filter by module (e.g., 'module-1-ros2')"
    )
    chapter_filter: Optional[str] = Field(
        default=None,
        description="Filter by chapter"
    )
    min_score: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="Minimum similarity score (0-1)"
    )
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
        description="OpenAI temperature (0-2)"
    )
    stream: bool = Field(
        default=False,
        description="Enable streaming response"
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and sanitize query."""
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")
        return v


class SelectionQueryRequest(BaseModel):
    """
    Request for selection-only RAG query.

    CRITICAL: This mode does NOT query Qdrant or use any book context.
    Only the provided selected_text is used to answer the question.
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question about the selection (1-2000 characters)"
    )
    selected_text: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="User's selected/highlighted text (10-5000 characters)"
    )
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
        description="OpenAI temperature (0-2)"
    )
    stream: bool = Field(
        default=False,
        description="Enable streaming response"
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and sanitize query."""
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")
        return v

    @field_validator('selected_text')
    @classmethod
    def validate_selected_text(cls, v: str) -> str:
        """Validate selected text."""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Selected text must be at least 10 characters")
        if len(v) > 5000:
            raise ValueError("Selected text cannot exceed 5000 characters")
        return v


class EmbedRequest(BaseModel):
    """Request to embed text."""
    texts: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Texts to embed (1-100 items)"
    )
    input_type: str = Field(
        default="search_document",
        description="Cohere input type (search_document or search_query)"
    )


class EmbedResponse(BaseModel):
    """Response with embeddings."""
    embeddings: List[List[float]]
    model: str
    dimension: int
    count: int


class CitationResponse(BaseModel):
    """Citation in API response."""
    chunk_id: str
    content: str
    source_path: str
    module: str
    chapter: str
    section: str
    score: float


class RAGQueryResponse(BaseModel):
    """Response from RAG query."""
    answer: str
    citations: List[CitationResponse]
    mode: str
    query: str
    token_usage: Dict[str, int] = {}
    processing_time_ms: float


class IngestRequest(BaseModel):
    """Request to ingest documents."""
    docs_path: str = Field(..., description="Path to the docs directory")
    single_file: Optional[str] = Field(
        default=None,
        description="Optional single file to ingest"
    )


class IngestInlineRequest(BaseModel):
    """Request to ingest documents inline (for cloud deployments)."""
    documents: List[Dict[str, Any]] = Field(
        ...,
        description="List of documents with 'content', 'source_path', 'module', 'chapter', 'section' fields"
    )


class IngestResponse(BaseModel):
    """Response from ingestion."""
    status: str
    documents_loaded: int = 0
    chunks_created: int = 0
    chunks_stored: int = 0
    errors: List[str] = []
    duration_seconds: float = 0


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """
    Query the book using RAG (Retrieval-Augmented Generation).

    **Book Mode** - This endpoint:
    1. Embeds the query using Cohere (embed-english-v3.0)
    2. Searches Qdrant for relevant chunks
    3. Generates a response using OpenAI with retrieved context
    4. Returns answer with citations

    Use `module_filter` to restrict search to a specific module.

    **Response Behavior:**
    - If no relevant content found: Returns "I couldn't find relevant information..."
    - Always includes citations when content is found
    - Never hallucinate or use information outside the book
    """
    start_time = datetime.utcnow()

    if request.stream:
        return await rag_query_stream(request)

    try:
        rag_service = get_rag_service()

        response = await rag_service.query_book_async(
            query=request.query,
            top_k=request.top_k,
            module_filter=request.module_filter,
            chapter_filter=request.chapter_filter,
            min_score=request.min_score,
            temperature=request.temperature,
        )

        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000

        return RAGQueryResponse(
            answer=response.answer,
            citations=[
                CitationResponse(
                    chunk_id=c.chunk_id,
                    content=c.content[:500] + "..." if len(c.content) > 500 else c.content,
                    source_path=c.source_path,
                    module=c.module,
                    chapter=c.chapter,
                    section=c.section,
                    score=c.score,
                )
                for c in response.citations
            ],
            mode=response.mode,
            query=response.query,
            token_usage=response.token_usage,
            processing_time_ms=processing_time,
        )

    except ValueError as e:
        # Input validation errors - safe to expose
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Internal errors - sanitize
        logger.error(f"RAG query error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Service temporarily unavailable. Please try again."
        )


@router.post("/query-selection", response_model=RAGQueryResponse)
async def rag_query_selection(request: SelectionQueryRequest):
    """
    Query using ONLY the selected text (Selection-Only Mode).

    **CRITICAL SECURITY:**
    - This endpoint does NOT query Qdrant
    - It does NOT use any book context
    - It answers ONLY based on the provided `selected_text`

    **Use Case:**
    When users highlight text and want to understand just that selection,
    without any additional context from the book.

    **Response Behavior:**
    - If selected text doesn't contain enough info to answer:
      Returns "The selected text does not contain enough information to answer this."
    - Never uses information outside the selected text
    - No citations from Qdrant (only the selection itself)
    """
    start_time = datetime.utcnow()

    if request.stream:
        return await rag_query_selection_stream(request)

    try:
        rag_service = get_rag_service()

        # CRITICAL: This ONLY uses selected_text, NEVER queries Qdrant
        response = await rag_service.query_selection_async(
            query=request.query,
            selected_text=request.selected_text,
            temperature=request.temperature,
        )

        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000

        return RAGQueryResponse(
            answer=response.answer,
            citations=[
                CitationResponse(
                    chunk_id=c.chunk_id,
                    content=c.content[:500] + "..." if len(c.content) > 500 else c.content,
                    source_path=c.source_path,
                    module=c.module,
                    chapter=c.chapter,
                    section=c.section,
                    score=c.score,
                )
                for c in response.citations
            ],
            mode=response.mode,
            query=response.query,
            token_usage=response.token_usage,
            processing_time_ms=processing_time,
        )

    except ValueError as e:
        # Input validation errors - safe to expose
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Internal errors - sanitize
        logger.error(f"Selection query error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Service temporarily unavailable. Please try again."
        )


async def rag_query_stream(request: RAGQueryRequest):
    """Stream a RAG query response."""
    async def generate():
        try:
            rag_service = get_rag_service()
            async for chunk in rag_service.stream_query_book(
                query=request.query,
                top_k=request.top_k,
                module_filter=request.module_filter,
                min_score=request.min_score,
                temperature=request.temperature,
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream error: {type(e).__name__}")
            yield f"data: {json.dumps({'error': 'Streaming error occurred'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


async def rag_query_selection_stream(request: SelectionQueryRequest):
    """Stream a selection-only query response."""
    async def generate():
        try:
            rag_service = get_rag_service()
            async for chunk in rag_service.stream_query_selection(
                query=request.query,
                selected_text=request.selected_text,
                temperature=request.temperature,
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Selection stream error: {type(e).__name__}")
            yield f"data: {json.dumps({'error': 'Streaming error occurred'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


@router.post("/embed", response_model=EmbedResponse)
async def embed_texts(request: EmbedRequest):
    """
    Generate embeddings for texts using Cohere.

    Useful for testing embeddings or custom similarity searches.
    Uses embed-english-v3.0 model (1024 dimensions).
    """
    try:
        embedding_service = get_embedding_service()
        embeddings = embedding_service.embed_documents(request.texts)

        return EmbedResponse(
            embeddings=embeddings,
            model=embedding_service.model,
            dimension=len(embeddings[0]) if embeddings else 0,
            count=len(embeddings),
        )

    except Exception as e:
        logger.error(f"Embed error: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Embedding service temporarily unavailable"
        )


@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
):
    """
    Ingest documents into the RAG system.

    This endpoint:
    1. Loads MDX/MD documents from the specified path
    2. Chunks them semantically
    3. Generates embeddings with Cohere
    4. Stores vectors in Qdrant

    For large document sets, this may take several minutes.
    """
    try:
        pipeline = IngestionPipeline(request.docs_path)

        if request.single_file:
            # Ingest single file synchronously
            result = pipeline.ingest_single_document(request.single_file)
            return IngestResponse(
                status="completed",
                chunks_created=result.get("chunks_created", 0),
                chunks_stored=result.get("chunks_stored", 0),
                errors=result.get("errors", []),
            )
        else:
            # Run full ingestion
            result = pipeline.run()
            return IngestResponse(
                status="completed",
                documents_loaded=result.get("documents_loaded", 0),
                chunks_created=result.get("chunks_created", 0),
                chunks_stored=result.get("chunks_stored", 0),
                errors=result.get("errors", []),
                duration_seconds=result.get("duration_seconds", 0),
            )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Path not found: {request.docs_path}")
    except Exception as e:
        logger.error(f"Ingest error: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Ingestion failed. Check logs for details."
        )


@router.post("/ingest-inline", response_model=IngestResponse)
async def ingest_inline(request: IngestInlineRequest):
    """
    Ingest documents inline (for cloud deployments without filesystem access).

    This endpoint accepts document content directly instead of reading from files.
    Each document should have:
    - content: The full text content
    - source_path: Original file path (for reference)
    - module: Module name (e.g., 'module-1-ros2')
    - chapter: Chapter name
    - section: Section name
    """
    try:
        from ..services.vectorstore import get_vectorstore_service
        from ..services.embeddings import get_embedding_service
        from ..ingestion.chunker import SemanticChunker
        import uuid

        vectorstore = get_vectorstore_service()
        embedding_service = get_embedding_service()
        chunker = SemanticChunker()

        chunks_created = 0
        chunks_stored = 0
        errors = []

        for doc in request.documents:
            try:
                content = doc.get("content", "")
                source_path = doc.get("source_path", "unknown")
                module = doc.get("module", "unknown")
                chapter = doc.get("chapter", "unknown")
                section = doc.get("section", "unknown")

                # Chunk the document using the proper method
                # Use the provided module/chapter if available, otherwise extract from source_path
                actual_module = module if module != "unknown" else "general"
                actual_chapter = chapter if chapter != "unknown" else source_path.split('/')[-1].replace('.mdx', '')

                # Extract module and chapter from source_path if not provided explicitly
                path_parts = source_path.split('/')
                if module == "unknown" and len(path_parts) >= 2 and path_parts[0].startswith('module'):
                    actual_module = path_parts[0]
                    actual_chapter = path_parts[1].replace('.mdx', '')

                # Use the chunk_document method which returns DocumentChunk objects
                document_chunks = chunker.chunk_document(
                    content=content,
                    document_path=source_path,
                    module=actual_module,
                    chapter=actual_chapter,
                    title=section
                )

                chunks_created += len(document_chunks)

                # Generate embeddings and store
                for i, doc_chunk in enumerate(document_chunks):
                    chunk_id = f"{source_path}_{i}_{uuid.uuid4().hex[:8]}"
                    embedding = embedding_service.embed_query(doc_chunk.content)

                    vectorstore.upsert_chunks(
                        chunk_ids=[chunk_id],
                        embeddings=[embedding],
                        payloads=[{
                            "content": doc_chunk.content,
                            "source_path": source_path,
                            "module": doc_chunk.module,
                            "chapter": doc_chunk.chapter,
                            "section": doc_chunk.section,
                            "chunk_index": i,
                            "chunk_type": doc_chunk.chunk_type,
                        }]
                    )
                    chunks_stored += 1

            except Exception as e:
                errors.append(f"Error processing {doc.get('source_path', 'unknown')}: {str(e)}")

        return IngestResponse(
            status="completed",
            documents_loaded=len(request.documents),
            chunks_created=chunks_created,
            chunks_stored=chunks_stored,
            errors=errors,
        )

    except Exception as e:
        logger.error(f"Inline ingest error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Ingestion failed. Check logs for details."
        )


@router.get("/stats")
async def get_stats():
    """
    Get statistics about the RAG system.

    Returns information about the vector store and configuration.
    Does NOT expose any credential values.
    """
    try:
        from ..services.vectorstore import get_vectorstore_service
        from ..config import get_settings

        settings = get_settings()
        vectorstore = get_vectorstore_service()
        collection_info = vectorstore.get_collection_info()

        return {
            "status": "healthy",
            "vectorstore": collection_info,
            "embedding": {
                "model": settings.cohere_embedding_model,
                "dimension": settings.cohere_embedding_dimension,
            },
            "chat": {
                "model": settings.openai_chat_model,
            },
            "chunking": {
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
            },
            "modes": {
                "book": "Full RAG with Qdrant vector search",
                "selection_only": "Uses ONLY provided text (no Qdrant)",
            },
        }

    except Exception as e:
        logger.error(f"Stats error: {type(e).__name__}")
        return {
            "status": "error",
            "message": "Unable to fetch stats",
        }


@router.delete("/clear")
async def clear_vectorstore():
    """
    Clear all vectors from the store (USE WITH CAUTION!).

    This will delete all indexed documents and require re-ingestion.
    """
    try:
        from ..services.vectorstore import get_vectorstore_service

        vectorstore = get_vectorstore_service()
        success = vectorstore.clear_collection()

        if success:
            return {"status": "cleared", "message": "Vector store cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear vector store")

    except Exception as e:
        logger.error(f"Clear error: {type(e).__name__}")
        raise HTTPException(
            status_code=500,
            detail="Failed to clear vector store"
        )
