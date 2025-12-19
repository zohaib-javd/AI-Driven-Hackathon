"""
RAG Query Service using OpenAI for chat completions.

SECURITY FEATURES:
- Strict mode isolation (selection mode NEVER queries Qdrant)
- Grounded responses only (no hallucination)
- Clear mode indicators in responses
- No credential exposure

MODES:
1. Book Mode - Full RAG with Cohere embeddings + Qdrant search + OpenAI
2. Selection-Only Mode - Uses ONLY user-highlighted text (NO Qdrant)
"""

import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field

from openai import OpenAI, AsyncOpenAI

from .embeddings import get_embedding_service, CohereEmbeddingService
from .vectorstore import get_vectorstore_service, QdrantService
from ..config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Represents a citation from the source material."""
    chunk_id: str
    content: str
    source_path: str
    module: str
    chapter: str
    section: str
    score: float
    start_index: Optional[int] = None
    end_index: Optional[int] = None


@dataclass
class RAGResponse:
    """Response from RAG query."""
    answer: str
    citations: List[Citation]
    mode: str  # "book" or "selection_only"
    query: str
    context_used: str
    token_usage: Dict[str, int] = field(default_factory=dict)


class RAGService:
    """
    RAG Query Service with strict mode isolation.

    CRITICAL: Selection-only mode NEVER queries Qdrant.
    This is a constitutional requirement for deterministic retrieval behavior.
    """

    # System prompt for Book Mode (full RAG)
    SYSTEM_PROMPT_BOOK = """You are an expert AI assistant for the Physical AI & Humanoid Robotics educational book.
Your role is to help users understand concepts from the book content.

CRITICAL INSTRUCTIONS:
1. Answer questions ONLY using the provided context from the book
2. If the context doesn't contain enough information, clearly state:
   "I couldn't find relevant information in the book to answer your question."
3. NEVER hallucinate or make up information not in the context
4. NEVER reference your training data - only use the provided context
5. Always cite your sources by referencing the module, chapter, and section

RESPONSE FORMAT:
- Use clear, educational language appropriate for learners
- Include relevant code examples from the context when applicable
- Format your response with markdown for readability
- When citing sources, use: [Module X: Chapter Title - Section Name]

TOPICS COVERED:
- Module 1: ROS 2 Fundamentals (Nodes, Topics, Services, URDF)
- Module 2: Digital Twin Simulation (Gazebo, Unity, Sensors)
- Module 3: NVIDIA Isaac (Sim, Nav2, Perception)
- Module 4: VLA (Vision-Language-Action, LLMs, Manipulation)"""

    # System prompt for Selection-Only Mode (STRICT - no external context)
    SYSTEM_PROMPT_SELECTION = """You are an expert AI assistant helping users understand specific text they have selected from a Physical AI & Humanoid Robotics educational book.

CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THESE EXACTLY:
1. Answer ONLY based on the selected text provided - NOTHING ELSE
2. DO NOT use any external knowledge, training data, or assumptions
3. DO NOT reference information outside the selected text
4. If the selected text doesn't contain enough information to answer, respond EXACTLY:
   "The selected text does not contain enough information to answer this."
5. Explain only what is explicitly stated in the selection

RESPONSE FORMAT:
- Be concise and focused on the selection
- If there are code examples in the selection, explain them
- Use markdown for readability
- Do not add information beyond what is in the selected text

The user has specifically highlighted this text and wants to understand ONLY this selection."""

    def __init__(
        self,
        embedding_service: Optional[CohereEmbeddingService] = None,
        vectorstore_service: Optional[QdrantService] = None,
    ):
        """Initialize the RAG service."""
        self.settings = get_settings()
        self.embedding_service = embedding_service or get_embedding_service()
        self.vectorstore_service = vectorstore_service or get_vectorstore_service()

        # Initialize OpenAI clients
        self.openai_client = OpenAI(api_key=self.settings.openai_api_key)
        self.openai_async_client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    def query_book(
        self,
        query: str,
        top_k: int = 5,
        module_filter: Optional[str] = None,
        chapter_filter: Optional[str] = None,
        min_score: float = 0.5,
        temperature: float = 0.7,
    ) -> RAGResponse:
        """
        Query the book using RAG (Retrieval-Augmented Generation).

        This is BOOK MODE which:
        1. Embeds the query using Cohere
        2. Searches Qdrant for relevant chunks
        3. Generates response using OpenAI with retrieved context
        4. Returns answer with citations

        Args:
            query: User's question
            top_k: Number of chunks to retrieve
            module_filter: Optional module to filter by
            chapter_filter: Optional chapter to filter by
            min_score: Minimum similarity score for retrieval
            temperature: OpenAI temperature for response generation

        Returns:
            RAGResponse with answer and citations
        """
        logger.info(f"[BOOK MODE] Query: {query[:50]}...")

        # Step 1: Embed the query using Cohere
        query_embedding = self.embedding_service.embed_query(query)

        # Step 2: Search Qdrant for relevant chunks
        search_results = self.vectorstore_service.search(
            query_embedding=query_embedding,
            top_k=top_k,
            module_filter=module_filter,
            chapter_filter=chapter_filter,
            min_score=min_score,
        )

        if not search_results:
            return RAGResponse(
                answer="I couldn't find relevant information in the book to answer your question. Could you try rephrasing or asking about a different topic covered in the Physical AI & Humanoid Robotics modules?\n\nNote: The knowledge base might be empty. Please ensure the book content has been ingested.",
                citations=[],
                mode="book",
                query=query,
                context_used="",
            )

        # Step 3: Build context and citations
        citations = []
        context_parts = []

        for i, result in enumerate(search_results):
            citation = Citation(
                chunk_id=result["chunk_id"],
                content=result["content"],
                source_path=result["source_path"],
                module=result["module"] or "Unknown",
                chapter=result["chapter"] or "Unknown",
                section=result["section"] or "Unknown",
                score=result["score"],
            )
            citations.append(citation)

            context_parts.append(
                f"[Source {i+1}: {citation.module} - {citation.chapter} - {citation.section}]\n{result['content']}"
            )

        context = "\n\n---\n\n".join(context_parts)

        # Step 4: Generate response with OpenAI
        response = self._generate_response(
            query=query,
            context=context,
            system_prompt=self.SYSTEM_PROMPT_BOOK,
            temperature=temperature,
        )

        logger.info(f"[BOOK MODE] Found {len(citations)} citations")

        return RAGResponse(
            answer=response["answer"],
            citations=citations,
            mode="book",
            query=query,
            context_used=context,
            token_usage=response.get("token_usage", {}),
        )

    def query_selection(
        self,
        query: str,
        selected_text: str,
        temperature: float = 0.7,
    ) -> RAGResponse:
        """
        Query using ONLY the selected text (Selection-Only Mode).

        CRITICAL SECURITY:
        - This mode does NOT query Qdrant
        - This mode does NOT use any external context
        - Only the provided selected_text is used to answer the question

        Args:
            query: User's question about the selection
            selected_text: The text the user has selected/highlighted
            temperature: OpenAI temperature for response generation

        Returns:
            RAGResponse with answer (no Qdrant citations)
        """
        logger.info(f"[SELECTION MODE] Query about {len(selected_text)} chars of selected text")

        # CRITICAL: NO Qdrant query here - only use selected_text
        # This is a constitutional requirement

        if not selected_text or not selected_text.strip():
            return RAGResponse(
                answer="No text was selected. Please highlight some text from the book and try again.",
                citations=[],
                mode="selection_only",
                query=query,
                context_used="",
            )

        # Create a "citation" for the selected text (NOT from Qdrant)
        selection_citation = Citation(
            chunk_id="user_selection",
            content=selected_text,
            source_path="user_selected_text",
            module="User Selection",
            chapter="Selected Text",
            section="Highlighted Content",
            score=1.0,
        )

        # Build context from selection ONLY - NO QDRANT
        context = f"[User's Selected Text]\n{selected_text}"

        # Generate response using ONLY the selected text
        response = self._generate_response(
            query=query,
            context=context,
            system_prompt=self.SYSTEM_PROMPT_SELECTION,
            temperature=temperature,
        )

        logger.info("[SELECTION MODE] Response generated from selection only (no Qdrant)")

        return RAGResponse(
            answer=response["answer"],
            citations=[selection_citation],
            mode="selection_only",
            query=query,
            context_used=selected_text,
            token_usage=response.get("token_usage", {}),
        )

    def _generate_response(
        self,
        query: str,
        context: str,
        system_prompt: str,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Generate a response using OpenAI.

        Args:
            query: User's question
            context: Context to use for answering
            system_prompt: System prompt for the model
            temperature: Temperature for generation

        Returns:
            Dictionary with answer and token usage
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Context:\n\n{context}\n\n---\n\nQuestion: {query}",
            },
        ]

        try:
            response = self.openai_client.chat.completions.create(
                model=self.settings.openai_chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=1500,
            )

            return {
                "answer": response.choices[0].message.content,
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

        except Exception as e:
            logger.error(f"OpenAI API error: {type(e).__name__}")
            # SECURITY: Don't expose internal error details
            return {
                "answer": "I encountered an error while generating a response. Please try again.",
                "token_usage": {},
            }

    async def query_book_async(
        self,
        query: str,
        top_k: int = 5,
        module_filter: Optional[str] = None,
        chapter_filter: Optional[str] = None,
        min_score: float = 0.5,
        temperature: float = 0.7,
    ) -> RAGResponse:
        """Async version of query_book."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.query_book(
                query, top_k, module_filter, chapter_filter, min_score, temperature
            ),
        )

    async def query_selection_async(
        self,
        query: str,
        selected_text: str,
        temperature: float = 0.7,
    ) -> RAGResponse:
        """Async version of query_selection."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.query_selection(query, selected_text, temperature),
        )

    async def stream_query_book(
        self,
        query: str,
        top_k: int = 5,
        module_filter: Optional[str] = None,
        min_score: float = 0.5,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a RAG response for the book query.

        Yields:
            Chunks of the response as they are generated
        """
        logger.info(f"[BOOK MODE STREAM] Query: {query[:50]}...")

        # Embed query and search Qdrant
        query_embedding = self.embedding_service.embed_query(query)
        search_results = self.vectorstore_service.search(
            query_embedding=query_embedding,
            top_k=top_k,
            module_filter=module_filter,
            min_score=min_score,
        )

        if not search_results:
            yield "I couldn't find relevant information in the book to answer your question."
            return

        # Build context
        context_parts = []
        for i, result in enumerate(search_results):
            module = result.get("module", "Unknown")
            chapter = result.get("chapter", "Unknown")
            section = result.get("section", "Unknown")
            context_parts.append(
                f"[Source {i+1}: {module} - {chapter} - {section}]\n{result['content']}"
            )

        context = "\n\n---\n\n".join(context_parts)

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT_BOOK},
            {
                "role": "user",
                "content": f"Context:\n\n{context}\n\n---\n\nQuestion: {query}",
            },
        ]

        # Stream response
        try:
            stream = await self.openai_async_client.chat.completions.create(
                model=self.settings.openai_chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=1500,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

            # Yield citations at the end
            yield "\n\n---\n**Sources:**\n"
            for i, result in enumerate(search_results):
                module = result.get("module", "Unknown")
                section = result.get("section", "Unknown")
                yield f"- [{i+1}] {module}: {section}\n"

        except Exception as e:
            logger.error(f"Streaming error: {type(e).__name__}")
            yield "\n\nStreaming error occurred. Please try again."

    async def stream_query_selection(
        self,
        query: str,
        selected_text: str,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response for selection-only query.

        CRITICAL: This NEVER queries Qdrant - uses ONLY selected_text.

        Yields:
            Chunks of the response as they are generated
        """
        logger.info(f"[SELECTION MODE STREAM] Query about {len(selected_text)} chars")

        if not selected_text or not selected_text.strip():
            yield "No text was selected. Please highlight some text from the book and try again."
            return

        # CRITICAL: NO Qdrant query - only use selected_text
        context = f"[User's Selected Text]\n{selected_text}"

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT_SELECTION},
            {
                "role": "user",
                "content": f"Context:\n\n{context}\n\n---\n\nQuestion: {query}",
            },
        ]

        try:
            stream = await self.openai_async_client.chat.completions.create(
                model=self.settings.openai_chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=1500,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Selection streaming error: {type(e).__name__}")
            yield "\n\nStreaming error occurred. Please try again."


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
