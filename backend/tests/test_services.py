"""
Service layer tests for Physical AI RAG Backend.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestEmbeddingService:
    """Tests for embedding service."""

    @pytest.mark.asyncio
    async def test_embed_single_text(self, mock_openai_client):
        """Test embedding a single text."""
        with patch("src.services.embeddings.AsyncOpenAI", return_value=mock_openai_client):
            from src.services.embeddings import EmbeddingService

            service = EmbeddingService()
            result = await service.embed("Test text about ROS 2")

            assert result is not None
            assert len(result) == 3072  # text-embedding-3-large dimension

    @pytest.mark.asyncio
    async def test_embed_batch(self, mock_openai_client):
        """Test embedding multiple texts."""
        # Setup mock for batch embeddings
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * 3072),
            MagicMock(embedding=[0.2] * 3072),
            MagicMock(embedding=[0.3] * 3072),
        ]
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        with patch("src.services.embeddings.AsyncOpenAI", return_value=mock_openai_client):
            from src.services.embeddings import EmbeddingService

            service = EmbeddingService()
            texts = ["Text 1", "Text 2", "Text 3"]
            results = await service.embed_batch(texts)

            assert len(results) == 3
            for result in results:
                assert len(result) == 3072

    def test_count_tokens(self):
        """Test token counting."""
        with patch("src.services.embeddings.AsyncOpenAI"):
            from src.services.embeddings import EmbeddingService

            service = EmbeddingService()
            count = service.count_tokens("This is a test sentence.")

            assert count > 0
            assert isinstance(count, int)


class TestVectorStoreService:
    """Tests for vector store service."""

    @pytest.mark.asyncio
    async def test_initialize_creates_collection(self, mock_qdrant_client):
        """Test initialization creates collection if not exists."""
        with patch("src.services.vectorstore.QdrantClient", return_value=mock_qdrant_client):
            from src.services.vectorstore import VectorStoreService

            service = VectorStoreService()
            await service.initialize()

            mock_qdrant_client.get_collections.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_returns_results(self, mock_qdrant_client):
        """Test search returns formatted results."""
        with patch("src.services.vectorstore.QdrantClient", return_value=mock_qdrant_client):
            from src.services.vectorstore import VectorStoreService

            service = VectorStoreService()
            query_embedding = [0.1] * 3072

            results = await service.search(query_embedding, top_k=5)

            assert len(results) > 0
            assert results[0].score == 0.95
            assert "ROS 2" in results[0].content

    @pytest.mark.asyncio
    async def test_search_with_module_filter(self, mock_qdrant_client):
        """Test search with module filter."""
        with patch("src.services.vectorstore.QdrantClient", return_value=mock_qdrant_client):
            from src.services.vectorstore import VectorStoreService

            service = VectorStoreService()
            query_embedding = [0.1] * 3072

            results = await service.search(
                query_embedding,
                top_k=5,
                module_filter="module-1-ros2"
            )

            # Verify filter was applied (check the call)
            mock_qdrant_client.search.assert_called()


class TestRetrievalService:
    """Tests for retrieval service."""

    @pytest.mark.asyncio
    async def test_retrieve_context(self, mock_openai_client, mock_qdrant_client):
        """Test context retrieval."""
        with patch("src.services.embeddings.AsyncOpenAI", return_value=mock_openai_client):
            with patch("src.services.vectorstore.QdrantClient", return_value=mock_qdrant_client):
                from src.services.retrieval import RetrievalService

                service = RetrievalService()
                results, citations = await service.retrieve_context(
                    query="What are ROS 2 nodes?",
                    top_k=5
                )

                assert isinstance(results, list)
                assert isinstance(citations, list)

    def test_build_context_prompt(self, mock_openai_client, mock_qdrant_client):
        """Test context prompt building."""
        with patch("src.services.embeddings.AsyncOpenAI", return_value=mock_openai_client):
            with patch("src.services.vectorstore.QdrantClient", return_value=mock_qdrant_client):
                from src.services.retrieval import RetrievalService
                from src.models import SearchResult

                service = RetrievalService()

                results = [
                    SearchResult(
                        chunk_id="1",
                        document_id="doc-1",
                        content="ROS 2 nodes are the building blocks of robot applications.",
                        score=0.95,
                        metadata={"module": "module-1-ros2", "chapter": "ros2-nodes"}
                    )
                ]

                prompt = service.build_context_prompt(results)

                assert "ROS 2 nodes" in prompt
                assert isinstance(prompt, str)


class TestAgentService:
    """Tests for agent service."""

    @pytest.mark.asyncio
    async def test_chat_generates_response(self, mock_openai_client, mock_qdrant_client):
        """Test chat generates response with citations."""
        with patch("src.services.agent.AsyncOpenAI", return_value=mock_openai_client):
            with patch("src.services.embeddings.AsyncOpenAI", return_value=mock_openai_client):
                with patch("src.services.vectorstore.QdrantClient", return_value=mock_qdrant_client):
                    from src.services.agent import AgentService
                    from src.models import ChatRequest

                    service = AgentService()
                    request = ChatRequest(
                        message="What is ROS 2?",
                        include_citations=True,
                        max_context_chunks=5,
                        temperature=0.7,
                    )

                    response = await service.chat(request)

                    assert response is not None
                    assert response.message.content is not None
                    assert "ROS 2" in response.message.content

    @pytest.mark.asyncio
    async def test_suggest_topics(self, mock_openai_client):
        """Test topic suggestion."""
        # Setup mock for suggestions
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="- ROS 2 Nodes\n- Topics and Services\n- URDF Models"))
        ]
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("src.services.agent.AsyncOpenAI", return_value=mock_openai_client):
            with patch("src.services.embeddings.AsyncOpenAI", return_value=mock_openai_client):
                with patch("src.services.vectorstore.QdrantClient"):
                    from src.services.agent import AgentService

                    service = AgentService()
                    suggestions = await service.suggest_topics("How do I create a robot?", 3)

                    assert len(suggestions) == 3
                    assert "ROS 2 Nodes" in suggestions
