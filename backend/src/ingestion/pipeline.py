"""
Document ingestion pipeline.
Orchestrates loading, chunking, embedding, and storage.
"""

import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

from .loader import DocumentLoader, LoadedDocument
from .chunker import SemanticChunker, DocumentChunk
from ..services.embeddings import get_embedding_service, CohereEmbeddingService
from ..services.vectorstore import get_vectorstore_service, QdrantService
from ..config import get_settings

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Complete pipeline for ingesting documents into the RAG system.

    Steps:
    1. Load documents from docs directory
    2. Chunk documents into semantic sections
    3. Generate embeddings with Cohere
    4. Store vectors in Qdrant
    5. Store metadata in Postgres
    """

    def __init__(
        self,
        docs_path: str,
        embedding_service: Optional[CohereEmbeddingService] = None,
        vectorstore_service: Optional[QdrantService] = None,
    ):
        """
        Initialize the ingestion pipeline.

        Args:
            docs_path: Path to the docs directory
            embedding_service: Optional embedding service (uses singleton if not provided)
            vectorstore_service: Optional vector store service
        """
        self.settings = get_settings()
        self.docs_path = Path(docs_path)

        # Initialize services
        self.embedding_service = embedding_service or get_embedding_service()
        self.vectorstore_service = vectorstore_service or get_vectorstore_service()

        # Initialize loader and chunker
        self.loader = DocumentLoader(str(self.docs_path))
        self.chunker = SemanticChunker(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )

    def run(self) -> Dict[str, Any]:
        """
        Run the complete ingestion pipeline synchronously.

        Returns:
            Dictionary with ingestion statistics
        """
        start_time = datetime.utcnow()
        stats = {
            'documents_loaded': 0,
            'chunks_created': 0,
            'chunks_embedded': 0,
            'chunks_stored': 0,
            'errors': [],
        }

        try:
            # Step 1: Initialize vector store collection
            logger.info("Initializing vector store collection...")
            self.vectorstore_service.initialize_collection()

            # Step 2: Load all documents
            logger.info(f"Loading documents from {self.docs_path}...")
            documents = self.loader.load_all_documents()
            stats['documents_loaded'] = len(documents)
            logger.info(f"Loaded {len(documents)} documents")

            if not documents:
                logger.warning("No documents found to ingest")
                return stats

            # Step 3: Chunk documents
            logger.info("Chunking documents...")
            all_chunks: List[DocumentChunk] = []
            for doc in documents:
                try:
                    chunks = self.chunker.chunk_document(
                        content=doc.content,
                        document_path=doc.file_path,
                        module=doc.module,
                        chapter=doc.chapter,
                        title=doc.title,
                    )
                    all_chunks.extend(chunks)
                except Exception as e:
                    error_msg = f"Error chunking {doc.file_path}: {e}"
                    logger.error(error_msg)
                    stats['errors'].append(error_msg)

            stats['chunks_created'] = len(all_chunks)
            logger.info(f"Created {len(all_chunks)} chunks")

            if not all_chunks:
                logger.warning("No chunks created")
                return stats

            # Step 4: Generate embeddings
            logger.info("Generating embeddings with Cohere...")
            chunk_texts = [chunk.content for chunk in all_chunks]
            embeddings = self.embedding_service.embed_documents(chunk_texts)
            stats['chunks_embedded'] = len(embeddings)
            logger.info(f"Generated {len(embeddings)} embeddings")

            # Step 5: Store in Qdrant
            logger.info("Storing vectors in Qdrant...")
            chunk_ids = [chunk.chunk_id for chunk in all_chunks]
            payloads = [
                {
                    'content': chunk.content,
                    'module': chunk.module,
                    'chapter': chunk.chapter,
                    'section': chunk.section,
                    'source_path': chunk.document_path,
                    'chunk_type': chunk.chunk_type,
                    'chunk_index': chunk.chunk_index,
                    'total_chunks': chunk.total_chunks,
                    'metadata': chunk.metadata,
                }
                for chunk in all_chunks
            ]

            stored_count = self.vectorstore_service.upsert_chunks(
                chunk_ids=chunk_ids,
                embeddings=embeddings,
                payloads=payloads,
            )
            stats['chunks_stored'] = stored_count
            logger.info(f"Stored {stored_count} chunks in Qdrant")

        except Exception as e:
            error_msg = f"Pipeline error: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)

        # Calculate duration
        end_time = datetime.utcnow()
        stats['duration_seconds'] = (end_time - start_time).total_seconds()
        stats['completed_at'] = end_time.isoformat()

        logger.info(f"Ingestion complete: {stats}")
        return stats

    async def run_async(self) -> Dict[str, Any]:
        """
        Run the ingestion pipeline asynchronously.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run)

    def ingest_single_document(self, file_path: str) -> Dict[str, Any]:
        """
        Ingest a single document.

        Args:
            file_path: Path to the document relative to docs_path

        Returns:
            Ingestion statistics for this document
        """
        full_path = self.docs_path / file_path
        stats = {
            'file_path': file_path,
            'chunks_created': 0,
            'chunks_stored': 0,
            'errors': [],
        }

        try:
            # Load document
            doc = self.loader.load_document(full_path)
            if not doc:
                raise ValueError(f"Failed to load document: {file_path}")

            # Chunk document
            chunks = self.chunker.chunk_document(
                content=doc.content,
                document_path=doc.file_path,
                module=doc.module,
                chapter=doc.chapter,
                title=doc.title,
            )
            stats['chunks_created'] = len(chunks)

            if not chunks:
                return stats

            # Generate embeddings
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_service.embed_documents(chunk_texts)

            # Store in Qdrant
            chunk_ids = [chunk.chunk_id for chunk in chunks]
            payloads = [
                {
                    'content': chunk.content,
                    'module': chunk.module,
                    'chapter': chunk.chapter,
                    'section': chunk.section,
                    'source_path': chunk.document_path,
                    'chunk_type': chunk.chunk_type,
                    'chunk_index': chunk.chunk_index,
                    'total_chunks': chunk.total_chunks,
                    'metadata': chunk.metadata,
                }
                for chunk in chunks
            ]

            stored_count = self.vectorstore_service.upsert_chunks(
                chunk_ids=chunk_ids,
                embeddings=embeddings,
                payloads=payloads,
            )
            stats['chunks_stored'] = stored_count

        except Exception as e:
            error_msg = f"Error ingesting {file_path}: {e}"
            logger.error(error_msg)
            stats['errors'].append(error_msg)

        return stats

    def delete_document(self, source_path: str) -> bool:
        """
        Delete a document and its chunks from the vector store.

        Args:
            source_path: Path to the source document

        Returns:
            True if deletion was successful
        """
        return self.vectorstore_service.delete_by_source(source_path)

    def get_stats(self) -> Dict[str, Any]:
        """Get current ingestion statistics."""
        collection_info = self.vectorstore_service.get_collection_info()

        return {
            'docs_path': str(self.docs_path),
            'collection_info': collection_info,
            'embedding_model': self.settings.cohere_embedding_model,
            'embedding_dimension': self.settings.cohere_embedding_dimension,
            'chunk_size': self.settings.chunk_size,
            'chunk_overlap': self.settings.chunk_overlap,
        }


def run_ingestion(docs_path: str) -> Dict[str, Any]:
    """
    Convenience function to run ingestion.

    Args:
        docs_path: Path to the docs directory

    Returns:
        Ingestion statistics
    """
    pipeline = IngestionPipeline(docs_path)
    return pipeline.run()
