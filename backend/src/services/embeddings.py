"""
Embedding service using OpenAI's text-embedding models.
Handles text embedding generation with batching and caching.
"""

import asyncio
from typing import List, Optional
import logging

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import tiktoken

from ..config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using OpenAI."""

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.openai_embedding_model
        self._tokenizer = None

    @property
    def tokenizer(self):
        """Lazy-load tokenizer."""
        if self._tokenizer is None:
            try:
                self._tokenizer = tiktoken.encoding_for_model(self.model)
            except KeyError:
                self._tokenizer = tiktoken.get_encoding("cl100k_base")
        return self._tokenizer

    def count_tokens(self, text: str) -> int:
        """Count tokens in a text string."""
        return len(self.tokenizer.encode(text))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Vector embedding as list of floats
        """
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100,
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts with batching.

        Args:
            texts: List of texts to embed
            batch_size: Maximum texts per API call

        Returns:
            List of vector embeddings
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            logger.info(f"Embedding batch {i // batch_size + 1}, size: {len(batch)}")

            response = await self.client.embeddings.create(
                model=self.model,
                input=batch,
            )

            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

            # Small delay to avoid rate limits
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)

        return all_embeddings

    async def embed_with_metadata(
        self,
        texts: List[str],
    ) -> dict:
        """Generate embeddings with usage metadata.

        Args:
            texts: List of texts to embed

        Returns:
            Dict with embeddings and usage info
        """
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
        )

        return {
            "embeddings": [item.embedding for item in response.data],
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
