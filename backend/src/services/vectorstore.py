"""
Vector store service using Qdrant for similarity search.
Handles document storage, indexing, and retrieval.
"""

from typing import Dict, List, Optional
import logging
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from ..config import get_settings
from ..models import DocumentChunk, SearchResult

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for vector storage and similarity search using Qdrant."""

    # Dimension for text-embedding-3-large
    EMBEDDING_DIMENSION = 3072

    def __init__(self):
        self.settings = get_settings()
        self.collection_name = self.settings.qdrant_collection_name

        # Initialize Qdrant client
        if self.settings.qdrant_api_key:
            self.client = QdrantClient(
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key,
            )
        else:
            # Local Qdrant instance
            self.client = QdrantClient(url=self.settings.qdrant_url)

    async def initialize(self):
        """Initialize the vector collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            logger.info(f"Creating collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.EMBEDDING_DIMENSION,
                    distance=Distance.COSINE,
                ),
            )

            # Create payload indexes for filtering
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="module",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="chapter",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="document_type",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            logger.info(f"Collection {self.collection_name} created with indexes")
        else:
            logger.info(f"Collection {self.collection_name} already exists")

    async def upsert_chunks(
        self,
        chunks: List[DocumentChunk],
    ) -> int:
        """Insert or update document chunks with their embeddings.

        Args:
            chunks: List of document chunks with embeddings

        Returns:
            Number of chunks upserted
        """
        if not chunks:
            return 0

        points = []
        for chunk in chunks:
            if chunk.embedding is None:
                logger.warning(f"Chunk {chunk.id} has no embedding, skipping")
                continue

            point = PointStruct(
                id=chunk.id,
                vector=chunk.embedding,
                payload={
                    "content": chunk.content,
                    "document_id": chunk.metadata.document_id,
                    "module": chunk.metadata.module,
                    "chapter": chunk.metadata.chapter,
                    "chapter_title": chunk.metadata.chapter_title,
                    "section": chunk.metadata.section,
                    "document_type": chunk.metadata.document_type.value,
                    "chunk_index": chunk.metadata.chunk_index,
                    "total_chunks": chunk.metadata.total_chunks,
                    "has_code": chunk.metadata.has_code,
                    "has_diagram": chunk.metadata.has_diagram,
                    "token_count": chunk.token_count,
                },
            )
            points.append(point)

        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
            )
            logger.info(f"Upserted {len(points)} chunks to {self.collection_name}")

        return len(points)

    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        module_filter: Optional[str] = None,
        min_score: float = 0.5,
    ) -> List[SearchResult]:
        """Search for similar chunks.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            module_filter: Optional module to filter by
            min_score: Minimum similarity score

        Returns:
            List of search results
        """
        # Build filter if needed
        search_filter = None
        if module_filter:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="module",
                        match=MatchValue(value=module_filter),
                    )
                ]
            )

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=top_k,
            score_threshold=min_score,
        )

        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    chunk_id=str(result.id),
                    document_id=result.payload.get("document_id", ""),
                    content=result.payload.get("content", ""),
                    score=result.score,
                    metadata={
                        "module": result.payload.get("module"),
                        "chapter": result.payload.get("chapter"),
                        "chapter_title": result.payload.get("chapter_title"),
                        "section": result.payload.get("section"),
                        "has_code": result.payload.get("has_code"),
                    },
                )
            )

        return search_results

    async def delete_by_document(self, document_id: str) -> int:
        """Delete all chunks for a document.

        Args:
            document_id: Document ID to delete chunks for

        Returns:
            Number of chunks deleted
        """
        result = self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )
        logger.info(f"Deleted chunks for document: {document_id}")
        return result

    async def get_collection_info(self) -> Dict:
        """Get information about the collection."""
        info = self.client.get_collection(self.collection_name)
        return {
            "name": self.collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "status": info.status.value,
        }


# Singleton instance
_vectorstore_service: Optional[VectorStoreService] = None


def get_vectorstore_service() -> VectorStoreService:
    """Get or create vector store service instance."""
    global _vectorstore_service
    if _vectorstore_service is None:
        _vectorstore_service = VectorStoreService()
    return _vectorstore_service
