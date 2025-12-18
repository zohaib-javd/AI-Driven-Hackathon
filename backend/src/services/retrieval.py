"""
RAG retrieval service for the Physical AI chatbot.
Handles semantic search and context building.
"""

from typing import List, Optional, Tuple
import logging

from ..config import get_settings
from ..models import SearchResult, Citation
from .embeddings import get_embedding_service
from .vectorstore import get_vectorstore_service

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service for RAG retrieval and context building."""

    def __init__(self):
        self.settings = get_settings()
        self.embedding_service = get_embedding_service()
        self.vectorstore = get_vectorstore_service()

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
        module_filter: Optional[str] = None,
        min_score: float = 0.5,
    ) -> Tuple[List[SearchResult], List[Citation]]:
        """Retrieve relevant context for a query.

        Args:
            query: User query
            top_k: Number of chunks to retrieve
            module_filter: Optional module to filter by
            min_score: Minimum similarity score

        Returns:
            Tuple of (search results, citations)
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)

        # Search vector store
        results = await self.vectorstore.search(
            query_embedding=query_embedding,
            top_k=top_k,
            module_filter=module_filter,
            min_score=min_score,
        )

        # Build citations
        citations = []
        for result in results:
            citation = Citation(
                document_id=result.document_id,
                chunk_id=result.chunk_id,
                module=result.metadata.get("module", ""),
                chapter=result.metadata.get("chapter", ""),
                chapter_title=result.metadata.get("chapter_title", ""),
                relevance_score=result.score,
                excerpt=self._truncate_excerpt(result.content, 200),
            )
            citations.append(citation)

        return results, citations

    def build_context_prompt(
        self,
        results: List[SearchResult],
        max_tokens: int = 3000,
    ) -> str:
        """Build context prompt from search results.

        Args:
            results: Search results to include
            max_tokens: Maximum tokens for context

        Returns:
            Formatted context string
        """
        if not results:
            return ""

        context_parts = []
        current_tokens = 0

        for i, result in enumerate(results, 1):
            # Rough token estimate (4 chars per token)
            chunk_tokens = len(result.content) // 4

            if current_tokens + chunk_tokens > max_tokens:
                break

            source = f"[{result.metadata.get('chapter_title', 'Unknown')}]"
            context_parts.append(
                f"--- Source {i}: {source} ---\n{result.content}\n"
            )
            current_tokens += chunk_tokens

        return "\n".join(context_parts)

    def _truncate_excerpt(self, text: str, max_length: int) -> str:
        """Truncate text to max length at word boundary."""
        if len(text) <= max_length:
            return text

        truncated = text[:max_length]
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]

        return truncated + "..."

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        module_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        """Perform hybrid search combining semantic and keyword matching.

        Args:
            query: Search query
            top_k: Number of results
            module_filter: Optional module filter

        Returns:
            Ranked search results
        """
        # For now, just use semantic search
        # TODO: Add keyword search with BM25 or similar
        query_embedding = await self.embedding_service.embed_text(query)

        results = await self.vectorstore.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Get more for reranking
            module_filter=module_filter,
            min_score=0.3,  # Lower threshold for hybrid
        )

        # Rerank based on query term overlap (simple keyword boost)
        query_terms = set(query.lower().split())

        def score_with_keyword_boost(result: SearchResult) -> float:
            content_terms = set(result.content.lower().split())
            overlap = len(query_terms & content_terms)
            keyword_boost = overlap * 0.05  # Small boost per matching term
            return result.score + keyword_boost

        results.sort(key=score_with_keyword_boost, reverse=True)

        return results[:top_k]


# Singleton instance
_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    """Get or create retrieval service instance."""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service
