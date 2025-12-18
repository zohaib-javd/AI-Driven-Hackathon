"""
Embedding service using Cohere's embed models.
Handles text embedding generation with batching and caching.
Cohere provides high-quality embeddings optimized for retrieval.
"""

import asyncio
from typing import List, Optional
import logging

import cohere
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings

logger = logging.getLogger(__name__)


class CohereEmbeddingService:
    """
    Service for generating text embeddings using Cohere.

    Cohere's embed-english-v3.0 provides:
    - 1024-dimensional embeddings
    - Optimized for search/retrieval tasks
    - Support for different input types (search_document, search_query)
    """

    def __init__(self):
        self.settings = get_settings()
        self.client = cohere.Client(api_key=self.settings.cohere_api_key)
        self.model = self.settings.cohere_embedding_model
        self.dimension = self.settings.cohere_embedding_dimension

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    def embed_text(
        self,
        text: str,
        input_type: str = "search_document"
    ) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            input_type: Either "search_document" for indexing or "search_query" for queries

        Returns:
            Vector embedding as list of floats
        """
        response = self.client.embed(
            texts=[text],
            model=self.model,
            input_type=input_type,
            truncate="END",
        )
        return response.embeddings[0]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    def embed_batch(
        self,
        texts: List[str],
        input_type: str = "search_document",
        batch_size: int = 96,  # Cohere's max batch size
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with batching.

        Args:
            texts: List of texts to embed
            input_type: Either "search_document" for indexing or "search_query" for queries
            batch_size: Maximum texts per API call (Cohere max is 96)

        Returns:
            List of vector embeddings
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            logger.info(f"Embedding batch {i // batch_size + 1}/{(len(texts) + batch_size - 1) // batch_size}, size: {len(batch)}")

            response = self.client.embed(
                texts=batch,
                model=self.model,
                input_type=input_type,
                truncate="END",
            )

            all_embeddings.extend(response.embeddings)

            # Small delay to avoid rate limits
            if i + batch_size < len(texts):
                import time
                time.sleep(0.1)

        return all_embeddings

    async def embed_text_async(
        self,
        text: str,
        input_type: str = "search_document"
    ) -> List[float]:
        """
        Async wrapper for embed_text.
        Runs the sync Cohere client in a thread pool.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.embed_text(text, input_type)
        )

    async def embed_batch_async(
        self,
        texts: List[str],
        input_type: str = "search_document",
        batch_size: int = 96,
    ) -> List[List[float]]:
        """
        Async wrapper for embed_batch.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.embed_batch(texts, input_type, batch_size)
        )

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.
        Uses input_type="search_query" for optimal retrieval performance.
        """
        return self.embed_text(query, input_type="search_query")

    async def embed_query_async(self, query: str) -> List[float]:
        """Async version of embed_query."""
        return await self.embed_text_async(query, input_type="search_query")

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Generate embeddings for documents to be indexed.
        Uses input_type="search_document" for optimal storage.
        """
        return self.embed_batch(documents, input_type="search_document")

    async def embed_documents_async(self, documents: List[str]) -> List[List[float]]:
        """Async version of embed_documents."""
        return await self.embed_batch_async(documents, input_type="search_document")

    def embed_with_metadata(self, texts: List[str], input_type: str = "search_document") -> dict:
        """
        Generate embeddings with metadata.

        Args:
            texts: List of texts to embed
            input_type: Document or query type

        Returns:
            Dict with embeddings and metadata
        """
        response = self.client.embed(
            texts=texts,
            model=self.model,
            input_type=input_type,
            truncate="END",
        )

        return {
            "embeddings": response.embeddings,
            "model": self.model,
            "dimension": self.dimension,
            "input_type": input_type,
            "count": len(texts),
        }


# Singleton instance
_embedding_service: Optional[CohereEmbeddingService] = None


def get_embedding_service() -> CohereEmbeddingService:
    """Get or create embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = CohereEmbeddingService()
    return _embedding_service


# Backwards compatibility alias
EmbeddingService = CohereEmbeddingService
