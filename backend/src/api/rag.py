"""
RAG API endpoints for the Physical AI RAG Chatbot.
Implements both standard RAG queries and selection-only mode.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import json
from datetime import datetime

from ..services.rag import get_rag_service, RAGResponse, Citation
from ..services.embeddings import get_embedding_service
from ..ingestion import IngestionPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["RAG"])


# Request/Response Models
class RAGQueryRequest(BaseModel):
    """Request for standard RAG query."""
    query: str = Field(..., min_length=1, max_length=2000, description="User's question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    module_filter: Optional[str] = Field(default=None, description="Filter by module (e.g., 'module-1-ros2')")
    chapter_filter: Optional[str] = Field(default=None, description="Filter by chapter")
    min_score: float = Field(default=0.5, ge=0, le=1, description="Minimum similarity score")
    temperature: float = Field(default=0.7, ge=0, le=2, description="OpenAI temperature")
    stream: bool = Field(default=False, description="Enable streaming response")


class SelectionQueryRequest(BaseModel):
    """Request for selection-only RAG query."""
    query: str = Field(..., min_length=1, max_length=2000, description="User's question about the selection")
    selected_text: str = Field(..., min_length=1, max_length=10000, description="User's selected/highlighted text")
    temperature: float = Field(default=0.7, ge=0, le=2, description="OpenAI temperature")
    stream: bool = Field(default=False, description="Enable streaming response")


class EmbedRequest(BaseModel):
    """Request to embed text."""
    texts: List[str] = Field(..., min_length=1, max_length=100, description="Texts to embed")
    input_type: str = Field(default="search_document", description="Cohere input type")


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
    single_file: Optional[str] = Field(default=None, description="Optional single file to ingest")


class IngestResponse(BaseModel):
    """Response from ingestion."""
    status: str
    documents_loaded: int = 0
    chunks_created: int = 0
    chunks_stored: int = 0
    errors: List[str] = []
    duration_seconds: float = 0


# Endpoints

@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """
    Query the book using RAG (Retrieval-Augmented Generation).

    This endpoint:
    1. Embeds the query using Cohere
    2. Searches Qdrant for relevant chunks
    3. Generates a response using OpenAI with retrieved context

    Use `module_filter` to restrict search to a specific module.
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

    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query-selection", response_model=RAGQueryResponse)
async def rag_query_selection(request: SelectionQueryRequest):
    """
    Query using ONLY the selected text (Selection-Only Mode).

    CRITICAL: This endpoint does NOT query Qdrant or use any book context.
    It answers ONLY based on the provided selected_text.

    Use this when users highlight text and want to understand just that selection.
    """
    start_time = datetime.utcnow()

    if request.stream:
        return await rag_query_selection_stream(request)

    try:
        rag_service = get_rag_service()

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

    except Exception as e:
        logger.error(f"Selection query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

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
            logger.error(f"Selection stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


@router.post("/embed", response_model=EmbedResponse)
async def embed_texts(request: EmbedRequest):
    """
    Generate embeddings for texts using Cohere.

    Useful for testing embeddings or custom similarity searches.
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
        logger.error(f"Embed error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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

    For large document sets, this runs in the background.
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

    except Exception as e:
        logger.error(f"Ingest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """
    Get statistics about the RAG system.

    Returns information about the vector store and configuration.
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
        }

    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "status": "error",
            "error": str(e),
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
        logger.error(f"Clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
