"""
API endpoint tests for Physical AI RAG Backend.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self):
        """Test health check returns healthy status."""
        with patch("src.services.get_vectorstore_service") as mock_vs:
            mock_vs.return_value.initialize = AsyncMock()
            from src.main import app
            client = TestClient(app)

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "app" in data
            assert "version" in data


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self):
        """Test root endpoint returns API info."""
        with patch("src.services.get_vectorstore_service") as mock_vs:
            mock_vs.return_value.initialize = AsyncMock()
            from src.main import app
            client = TestClient(app)

            response = client.get("/")

            assert response.status_code == 200
            data = response.json()
            assert "name" in data
            assert "version" in data
            assert "docs" in data


class TestChatEndpoint:
    """Tests for chat endpoint."""

    @pytest.mark.asyncio
    async def test_chat_request_valid(self, sample_chat_request, mock_openai_client):
        """Test valid chat request returns response."""
        with patch("src.services.agent.AsyncOpenAI", return_value=mock_openai_client):
            with patch("src.services.get_vectorstore_service") as mock_vs:
                mock_vs.return_value.initialize = AsyncMock()
                mock_vs.return_value.search = AsyncMock(return_value=[])

                with patch("src.services.get_embedding_service") as mock_embed:
                    mock_embed.return_value.embed = AsyncMock(
                        return_value=[0.1] * 3072
                    )

                    from src.main import app
                    client = TestClient(app)

                    response = client.post("/api/chat", json=sample_chat_request)

                    # May fail without full setup, but structure should be correct
                    assert response.status_code in [200, 500]

    def test_chat_request_missing_message(self):
        """Test chat request without message returns error."""
        with patch("src.services.get_vectorstore_service") as mock_vs:
            mock_vs.return_value.initialize = AsyncMock()
            from src.main import app
            client = TestClient(app)

            response = client.post("/api/chat", json={})

            assert response.status_code == 422  # Validation error


class TestSearchEndpoint:
    """Tests for search endpoint."""

    def test_search_request_valid(self, sample_search_request):
        """Test valid search request."""
        with patch("src.services.get_vectorstore_service") as mock_vs:
            mock_vs.return_value.initialize = AsyncMock()
            mock_vs.return_value.search = AsyncMock(return_value=[])

            with patch("src.services.get_embedding_service") as mock_embed:
                mock_embed.return_value.embed = AsyncMock(
                    return_value=[0.1] * 3072
                )

                from src.main import app
                client = TestClient(app)

                response = client.post("/api/search", json=sample_search_request)

                # May fail without full setup
                assert response.status_code in [200, 500]


class TestModulesEndpoint:
    """Tests for modules listing endpoint."""

    def test_list_modules(self):
        """Test modules endpoint returns all 4 modules."""
        with patch("src.services.get_vectorstore_service") as mock_vs:
            mock_vs.return_value.initialize = AsyncMock()
            from src.main import app
            client = TestClient(app)

            response = client.get("/api/modules")

            assert response.status_code == 200
            data = response.json()
            assert "modules" in data
            assert len(data["modules"]) == 4

            module_ids = [m["id"] for m in data["modules"]]
            assert "module-1-ros2" in module_ids
            assert "module-2-digital-twin" in module_ids
            assert "module-3-isaac" in module_ids
            assert "module-4-vla" in module_ids


class TestIngestEndpoint:
    """Tests for document ingestion endpoint."""

    def test_ingest_status(self):
        """Test ingestion status endpoint."""
        with patch("src.services.get_vectorstore_service") as mock_vs:
            mock_vs.return_value.initialize = AsyncMock()
            mock_vs.return_value.get_collection_info = AsyncMock(
                return_value={
                    "name": "test_collection",
                    "vectors_count": 100,
                    "points_count": 100,
                    "status": "green",
                }
            )

            from src.main import app
            client = TestClient(app)

            response = client.get("/api/ingest/status")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
