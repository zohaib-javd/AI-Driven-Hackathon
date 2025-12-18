"""
Pytest configuration and fixtures for Physical AI RAG Backend tests.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["OPENAI_API_KEY"] = "test-api-key"
os.environ["DEBUG"] = "true"


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = MagicMock()

    # Mock embeddings
    mock_embedding_response = MagicMock()
    mock_embedding_response.data = [MagicMock(embedding=[0.1] * 3072)]
    client.embeddings.create = AsyncMock(return_value=mock_embedding_response)

    # Mock chat completions
    mock_chat_response = MagicMock()
    mock_chat_response.choices = [
        MagicMock(message=MagicMock(content="Test response about ROS 2"))
    ]
    mock_chat_response.usage = MagicMock(total_tokens=100)
    client.chat.completions.create = AsyncMock(return_value=mock_chat_response)

    return client


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing."""
    client = MagicMock()

    # Mock collection operations
    client.get_collections.return_value = MagicMock(collections=[])
    client.create_collection = MagicMock()
    client.upsert = MagicMock()

    # Mock search
    client.search.return_value = [
        MagicMock(
            id="test-id",
            score=0.95,
            payload={
                "content": "Test content about ROS 2 nodes",
                "document_id": "doc-1",
                "module": "module-1-ros2",
                "chapter": "ros2-nodes",
                "chapter_title": "ROS 2 Nodes",
                "section": "Introduction",
                "has_code": True,
            }
        )
    ]

    return client


@pytest.fixture
def sample_mdx_content():
    """Sample MDX content for testing document processing."""
    return '''---
title: "Test Chapter"
sidebar_position: 1
description: "A test chapter for unit testing"
---

# Test Chapter

This is a test chapter about ROS 2.

## Introduction

ROS 2 is a set of software libraries and tools for building robot applications.

```python
import rclpy
from rclpy.node import Node

class TestNode(Node):
    def __init__(self):
        super().__init__('test_node')
        self.get_logger().info('Test node started')
```

## Summary

This concludes the test chapter.
'''


@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing."""
    return {
        "message": "What is ROS 2?",
        "session_id": "test-session",
        "include_citations": True,
        "max_context_chunks": 5,
        "temperature": 0.7,
    }


@pytest.fixture
def sample_search_request():
    """Sample search request for testing."""
    return {
        "query": "ROS 2 nodes",
        "top_k": 5,
        "module_filter": None,
        "min_score": 0.5,
    }
