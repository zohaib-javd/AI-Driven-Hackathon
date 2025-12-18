"""
Vector store service using Qdrant Cloud for similarity search.
Handles document storage, indexing, and retrieval.
Optimized for Cohere embeddings (1024 dimensions).
"""

from typing import Dict, List, Optional, Any
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
    UpdateStatus,
)

from ..config import get_settings

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Service for vector storage and similarity search using Qdrant.
    Configured for Cohere embed-english-v3.0 (1024 dimensions).
    """

    def __init__(self):
        self.settings = get_settings()
        self.collection_name = self.settings.qdrant_collection_name
        self.embedding_dimension = self.settings.cohere_embedding_dimension

        # Initialize Qdrant client
        if self.settings.qdrant_api_key:
            # Qdrant Cloud
            self.client = QdrantClient(
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key,
                timeout=60,
            )
            logger.info(f"Connected to Qdrant Cloud: {self.settings.qdrant_url}")
        else:
            # Local Qdrant instance
            self.client = QdrantClient(url=self.settings.qdrant_url)
            logger.info(f"Connected to local Qdrant: {self.settings.qdrant_url}")

    def initialize_collection(self) -> bool:
        """
        Initialize the vector collection if it doesn't exist.
        Creates indexes for filtering by module, chapter, etc.

        Returns:
            True if collection was created, False if it already exists
        """
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            logger.info(f"Creating collection: {self.collection_name}")

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE,
                ),
                optimizers_config=models.OptimizersConfigDiff(
                    indexing_threshold=10000,
                ),
            )

            # Create payload indexes for efficient filtering
            indexes = ["module", "chapter", "section", "chunk_type", "source_path"]
            for field in indexes:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                )

            logger.info(f"Collection {self.collection_name} created with indexes")
            return True

        logger.info(f"Collection {self.collection_name} already exists")
        return False

    async def initialize_collection_async(self) -> bool:
        """Async wrapper for initialize_collection."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.initialize_collection)

    def upsert_chunks(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        payloads: List[Dict[str, Any]],
    ) -> int:
        """
        Insert or update document chunks with their embeddings.

        Args:
            chunk_ids: List of unique chunk identifiers
            embeddings: List of embedding vectors (1024 dimensions for Cohere)
            payloads: List of metadata dictionaries

        Returns:
            Number of chunks upserted
        """
        if not chunk_ids or not embeddings:
            return 0

        if len(chunk_ids) != len(embeddings) or len(chunk_ids) != len(payloads):
            raise ValueError("chunk_ids, embeddings, and payloads must have same length")

        points = []
        for chunk_id, embedding, payload in zip(chunk_ids, embeddings, payloads):
            point = PointStruct(
                id=chunk_id,
                vector=embedding,
                payload=payload,
            )
            points.append(point)

        # Batch upsert in chunks of 100
        batch_size = 100
        total_upserted = 0

        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            result = self.client.upsert(
                collection_name=self.collection_name,
                points=batch,
                wait=True,
            )
            if result.status == UpdateStatus.COMPLETED:
                total_upserted += len(batch)

        logger.info(f"Upserted {total_upserted} chunks to {self.collection_name}")
        return total_upserted

    async def upsert_chunks_async(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        payloads: List[Dict[str, Any]],
    ) -> int:
        """Async wrapper for upsert_chunks."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.upsert_chunks(chunk_ids, embeddings, payloads)
        )

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        module_filter: Optional[str] = None,
        chapter_filter: Optional[str] = None,
        min_score: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using cosine similarity.

        Args:
            query_embedding: Query vector from Cohere
            top_k: Number of results to return
            module_filter: Optional module to filter by
            chapter_filter: Optional chapter to filter by
            min_score: Minimum similarity score (0-1)

        Returns:
            List of search results with content, score, and metadata
        """
        # Build filter conditions
        must_conditions = []

        if module_filter:
            must_conditions.append(
                FieldCondition(
                    key="module",
                    match=MatchValue(value=module_filter),
                )
            )

        if chapter_filter:
            must_conditions.append(
                FieldCondition(
                    key="chapter",
                    match=MatchValue(value=chapter_filter),
                )
            )

        search_filter = Filter(must=must_conditions) if must_conditions else None

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=top_k,
            score_threshold=min_score,
            with_payload=True,
        )

        search_results = []
        for result in results:
            search_results.append({
                "chunk_id": str(result.id),
                "content": result.payload.get("content", ""),
                "score": result.score,
                "module": result.payload.get("module"),
                "chapter": result.payload.get("chapter"),
                "section": result.payload.get("section"),
                "source_path": result.payload.get("source_path"),
                "chunk_type": result.payload.get("chunk_type"),
                "metadata": result.payload,
            })

        return search_results

    async def search_async(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        module_filter: Optional[str] = None,
        chapter_filter: Optional[str] = None,
        min_score: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Async wrapper for search."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.search(query_embedding, top_k, module_filter, chapter_filter, min_score)
        )

    def delete_by_source(self, source_path: str) -> bool:
        """
        Delete all chunks from a specific source file.

        Args:
            source_path: Path to the source document

        Returns:
            True if deletion was successful
        """
        result = self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="source_path",
                            match=MatchValue(value=source_path),
                        )
                    ]
                )
            ),
        )
        logger.info(f"Deleted chunks for source: {source_path}")
        return result.status == UpdateStatus.COMPLETED

    def delete_by_module(self, module: str) -> bool:
        """Delete all chunks from a specific module."""
        result = self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(
                            key="module",
                            match=MatchValue(value=module),
                        )
                    ]
                )
            ),
        )
        logger.info(f"Deleted chunks for module: {module}")
        return result.status == UpdateStatus.COMPLETED

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status.value if info.status else "unknown",
                "embedding_dimension": self.embedding_dimension,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {
                "name": self.collection_name,
                "error": str(e),
            }

    def clear_collection(self) -> bool:
        """Delete and recreate the collection (use with caution!)."""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
            self.initialize_collection()
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            return False


# Singleton instance
_qdrant_service: Optional[QdrantService] = None


def get_vectorstore_service() -> QdrantService:
    """Get or create vector store service instance."""
    global _qdrant_service
    if _qdrant_service is None:
        _qdrant_service = QdrantService()
    return _qdrant_service


# Backwards compatibility alias
VectorStoreService = QdrantService
