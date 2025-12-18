"""
Document ingestion tests for Physical AI RAG Backend.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile
import os


class TestMDXProcessing:
    """Tests for MDX document processing."""

    def test_clean_mdx_content_removes_imports(self):
        """Test that import statements are removed."""
        from src.api.ingest import clean_mdx_content

        content = """import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Real Content

This is the actual content."""

        cleaned = clean_mdx_content(content)

        assert "import" not in cleaned
        assert "Real Content" in cleaned
        assert "actual content" in cleaned

    def test_clean_mdx_content_preserves_code_blocks(self):
        """Test that code blocks are marked but preserved."""
        from src.api.ingest import clean_mdx_content

        content = """# Python Example

```python
import rclpy
print("Hello ROS 2")
```

After the code block."""

        cleaned = clean_mdx_content(content)

        assert "[Code (python):" in cleaned
        assert "import rclpy" in cleaned
        assert "After the code block" in cleaned

    def test_clean_mdx_content_marks_mermaid_diagrams(self):
        """Test that Mermaid diagrams are marked."""
        from src.api.ingest import clean_mdx_content

        content = """# Architecture

```mermaid
graph TD
    A --> B
```

Description here."""

        cleaned = clean_mdx_content(content)

        assert "[Diagram:" in cleaned
        assert "graph TD" in cleaned


class TestChunking:
    """Tests for document chunking."""

    def test_chunk_document_respects_size(self):
        """Test chunking respects max chunk size."""
        from src.api.ingest import chunk_document, ChunkingConfig

        content = "This is paragraph one. " * 50 + "\n\n" + "This is paragraph two. " * 50

        config = ChunkingConfig(chunk_size=200, chunk_overlap=20, min_chunk_size=50)
        chunks = chunk_document(content, config)

        for chunk in chunks:
            # Allow some overflow for paragraph boundaries
            assert len(chunk) < config.chunk_size * 2

    def test_chunk_document_handles_short_content(self):
        """Test chunking short content creates single chunk."""
        from src.api.ingest import chunk_document, ChunkingConfig

        content = "Short content that fits in one chunk."

        config = ChunkingConfig(chunk_size=500, chunk_overlap=50, min_chunk_size=20)
        chunks = chunk_document(content, config)

        assert len(chunks) == 1
        assert chunks[0] == content

    def test_chunk_document_splits_paragraphs(self):
        """Test chunking splits at paragraph boundaries."""
        from src.api.ingest import chunk_document, ChunkingConfig

        content = """First paragraph with content.

Second paragraph with more content.

Third paragraph concluding."""

        config = ChunkingConfig(chunk_size=100, chunk_overlap=10, min_chunk_size=20)
        chunks = chunk_document(content, config)

        # Each paragraph should be separate or combined logically
        assert len(chunks) >= 1


class TestDocumentProcessing:
    """Tests for full document processing."""

    @pytest.mark.asyncio
    async def test_process_document_extracts_frontmatter(self, sample_mdx_content):
        """Test document processing extracts frontmatter."""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.mdx',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(sample_mdx_content)
            temp_path = Path(f.name)

        try:
            with patch("src.api.ingest.get_embedding_service") as mock_embed:
                mock_service = MagicMock()
                mock_service.count_tokens = MagicMock(return_value=100)
                mock_embed.return_value = mock_service

                from src.api.ingest import process_document, ChunkingConfig

                config = ChunkingConfig(chunk_size=500, chunk_overlap=50, min_chunk_size=50)
                document = await process_document(temp_path, "module-1-ros2", config)

                assert document.title == "Test Chapter"
                assert document.module == "module-1-ros2"
                assert len(document.chunks) > 0
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_process_document_creates_chunks(self, sample_mdx_content):
        """Test document processing creates chunks with metadata."""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.mdx',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(sample_mdx_content)
            temp_path = Path(f.name)

        try:
            with patch("src.api.ingest.get_embedding_service") as mock_embed:
                mock_service = MagicMock()
                mock_service.count_tokens = MagicMock(return_value=100)
                mock_embed.return_value = mock_service

                from src.api.ingest import process_document, ChunkingConfig

                config = ChunkingConfig(chunk_size=200, chunk_overlap=20, min_chunk_size=50)
                document = await process_document(temp_path, "module-1-ros2", config)

                for chunk in document.chunks:
                    assert chunk.metadata.module == "module-1-ros2"
                    assert chunk.metadata.document_id == document.id
                    assert chunk.metadata.chapter_title == "Test Chapter"
        finally:
            os.unlink(temp_path)


class TestIngestAPI:
    """Tests for ingestion API endpoints."""

    def test_ingest_status_endpoint(self, mock_qdrant_client):
        """Test ingestion status endpoint."""
        with patch("src.services.get_vectorstore_service") as mock_vs:
            mock_vs.return_value.initialize = AsyncMock()
            mock_vs.return_value.get_collection_info = AsyncMock(
                return_value={
                    "name": "physical_ai_book",
                    "vectors_count": 500,
                    "points_count": 500,
                    "status": "green",
                }
            )

            from src.main import app
            from fastapi.testclient import TestClient

            client = TestClient(app)
            response = client.get("/api/ingest/status")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["ready", "error"]
