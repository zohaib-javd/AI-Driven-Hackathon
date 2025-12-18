"""
Document ingestion API endpoints.
Handles MDX parsing, chunking, and indexing.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
import logging
from pathlib import Path
import frontmatter
import re
from uuid import uuid4

from ..models import Document, DocumentChunk, ChunkMetadata, DocumentType
from ..services import get_embedding_service, get_vectorstore_service
from ..config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


class IngestRequest(BaseModel):
    """Request to ingest documents."""
    docs_path: str = Field(..., description="Path to docs directory")
    force_reindex: bool = Field(default=False, description="Force reindexing all docs")


class IngestResponse(BaseModel):
    """Response from ingestion."""
    status: str
    documents_processed: int
    chunks_created: int
    errors: List[str]


class ChunkingConfig(BaseModel):
    """Configuration for document chunking."""
    chunk_size: int = 500
    chunk_overlap: int = 50
    min_chunk_size: int = 100


def clean_mdx_content(content: str) -> str:
    """Remove MDX-specific syntax for plain text extraction."""
    # Remove import statements
    content = re.sub(r'^import\s+.*$', '', content, flags=re.MULTILINE)

    # Remove JSX components (keep content inside)
    content = re.sub(r'<(\w+)[^>]*>(.*?)</\1>', r'\2', content, flags=re.DOTALL)

    # Remove self-closing JSX
    content = re.sub(r'<\w+[^>]*/>', '', content)

    # Remove frontmatter delimiters
    content = re.sub(r'^---\s*$', '', content, flags=re.MULTILINE)

    # Clean up Mermaid diagrams - keep description
    content = re.sub(
        r'```mermaid\s*(.*?)```',
        r'[Diagram: \1]',
        content,
        flags=re.DOTALL
    )

    # Keep code blocks but mark them
    def mark_code(match):
        lang = match.group(1) or 'code'
        code = match.group(2)
        return f'[Code ({lang}):\n{code}]'

    content = re.sub(
        r'```(\w+)?\s*(.*?)```',
        mark_code,
        content,
        flags=re.DOTALL
    )

    # Clean up multiple newlines
    content = re.sub(r'\n{3,}', '\n\n', content)

    return content.strip()


def chunk_document(
    content: str,
    config: ChunkingConfig,
) -> List[str]:
    """Split document into semantic chunks.

    Uses paragraph boundaries when possible, falls back to
    sentence boundaries, then character boundaries.
    """
    # Split by double newlines (paragraphs)
    paragraphs = content.split('\n\n')

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If adding this paragraph would exceed chunk size
        if len(current_chunk) + len(para) > config.chunk_size:
            if current_chunk and len(current_chunk) >= config.min_chunk_size:
                chunks.append(current_chunk.strip())

            # If paragraph itself is too long, split it
            if len(para) > config.chunk_size:
                # Split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > config.chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
            else:
                current_chunk = para
        else:
            current_chunk += "\n\n" + para if current_chunk else para

    # Add final chunk
    if current_chunk and len(current_chunk) >= config.min_chunk_size:
        chunks.append(current_chunk.strip())

    return chunks


async def process_document(
    file_path: Path,
    module: str,
    config: ChunkingConfig,
) -> Document:
    """Process a single MDX document.

    Args:
        file_path: Path to MDX file
        module: Module name
        config: Chunking configuration

    Returns:
        Processed document with chunks
    """
    # Read and parse frontmatter
    with open(file_path, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)

    raw_content = post.content
    metadata = post.metadata

    # Create document
    doc_id = str(uuid4())
    chapter = file_path.stem

    document = Document(
        id=doc_id,
        path=str(file_path),
        title=metadata.get('title', chapter),
        description=metadata.get('description'),
        raw_content=raw_content,
        frontmatter=metadata,
        module=module,
        sidebar_position=metadata.get('sidebar_position', 0),
    )

    # Clean content for chunking
    clean_content = clean_mdx_content(raw_content)

    # Check for code and diagrams
    has_code = '```' in raw_content
    has_diagram = 'mermaid' in raw_content.lower()

    # Chunk the document
    text_chunks = chunk_document(clean_content, config)

    # Create chunk objects
    embedding_service = get_embedding_service()

    for i, chunk_text in enumerate(text_chunks):
        chunk = DocumentChunk(
            id=f"{doc_id}_chunk_{i}",
            content=chunk_text,
            metadata=ChunkMetadata(
                document_id=doc_id,
                module=module,
                chapter=chapter,
                chapter_title=document.title,
                document_type=DocumentType.CHAPTER,
                chunk_index=i,
                total_chunks=len(text_chunks),
                has_code=has_code and '[Code' in chunk_text,
                has_diagram=has_diagram and '[Diagram' in chunk_text,
            ),
            token_count=embedding_service.count_tokens(chunk_text),
        )
        document.chunks.append(chunk)

    return document


@router.post("/documents", response_model=IngestResponse)
async def ingest_documents(
    request: IngestRequest,
    background_tasks: BackgroundTasks,
):
    """
    Ingest all MDX documents from the docs directory.

    Parses frontmatter, chunks content, generates embeddings,
    and stores in the vector database.
    """
    docs_path = Path(request.docs_path)

    if not docs_path.exists():
        raise HTTPException(status_code=404, detail="Docs path not found")

    # Find all MDX files
    mdx_files = list(docs_path.rglob("*.mdx"))

    if not mdx_files:
        raise HTTPException(status_code=404, detail="No MDX files found")

    logger.info(f"Found {len(mdx_files)} MDX files to process")

    # Process in background
    background_tasks.add_task(
        _process_documents,
        mdx_files,
        docs_path,
    )

    return IngestResponse(
        status="processing",
        documents_processed=0,
        chunks_created=0,
        errors=[],
    )


async def _process_documents(mdx_files: List[Path], docs_path: Path):
    """Background task to process all documents."""
    settings = get_settings()
    config = ChunkingConfig(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    embedding_service = get_embedding_service()
    vectorstore = get_vectorstore_service()

    # Initialize vector store
    await vectorstore.initialize()

    documents_processed = 0
    chunks_created = 0
    errors = []

    for file_path in mdx_files:
        try:
            # Determine module from path
            relative_path = file_path.relative_to(docs_path)
            parts = relative_path.parts

            if len(parts) >= 2:
                module = parts[0]  # e.g., "module-1-ros2"
            else:
                module = "general"

            # Process document
            document = await process_document(file_path, module, config)

            if not document.chunks:
                logger.warning(f"No chunks generated for {file_path}")
                continue

            # Generate embeddings for all chunks
            chunk_texts = [c.content for c in document.chunks]
            embeddings = await embedding_service.embed_batch(chunk_texts)

            # Attach embeddings to chunks
            for chunk, embedding in zip(document.chunks, embeddings):
                chunk.embedding = embedding

            # Store in vector database
            await vectorstore.upsert_chunks(document.chunks)

            documents_processed += 1
            chunks_created += len(document.chunks)

            logger.info(
                f"Processed {file_path.name}: "
                f"{len(document.chunks)} chunks"
            )

        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    logger.info(
        f"Ingestion complete: {documents_processed} docs, "
        f"{chunks_created} chunks, {len(errors)} errors"
    )


@router.get("/status")
async def get_ingestion_status():
    """Get current ingestion status and collection info."""
    try:
        vectorstore = get_vectorstore_service()
        info = await vectorstore.get_collection_info()
        return {
            "status": "ready",
            "collection": info,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and its chunks from the index."""
    try:
        vectorstore = get_vectorstore_service()
        await vectorstore.delete_by_document(document_id)
        return {"status": "deleted", "document_id": document_id}
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
