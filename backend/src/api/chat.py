"""
Chat API endpoints for the RAG chatbot.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Optional
import logging

from ..models import (
    ChatRequest,
    ChatResponse,
    SearchRequest,
    SearchResponse,
)
from ..services import get_agent_service, get_retrieval_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the RAG-powered assistant.

    The assistant answers questions about:
    - ROS 2 fundamentals
    - Gazebo and Unity simulation
    - NVIDIA Isaac Sim
    - Vision-Language-Action (VLA) systems

    Responses are grounded in the book content with citations.
    """
    try:
        agent = get_agent_service()
        response = await agent.chat(request)
        return response
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response for real-time output.

    Returns a text/event-stream with response chunks.
    """
    try:
        agent = get_agent_service()

        async def generate():
            async for chunk in agent.stream_chat(request):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
        )
    except Exception as e:
        logger.error(f"Stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Search the knowledge base for relevant content.

    Returns ranked results with similarity scores.
    """
    try:
        from datetime import datetime

        start = datetime.utcnow()
        retrieval = get_retrieval_service()

        results, _ = await retrieval.retrieve_context(
            query=request.query,
            top_k=request.top_k,
            module_filter=request.module_filter,
            min_score=request.min_score,
        )

        end = datetime.utcnow()
        processing_time = (end - start).total_seconds() * 1000

        return SearchResponse(
            results=results,
            query=request.query,
            total_results=len(results),
            processing_time_ms=processing_time,
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggest")
async def suggest_topics(query: str, n: int = 3):
    """
    Get suggested topics related to a query.

    Useful for guiding users to relevant content.
    """
    try:
        agent = get_agent_service()
        suggestions = await agent.suggest_topics(query, n)
        return {"suggestions": suggestions}
    except Exception as e:
        logger.error(f"Suggest error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modules")
async def list_modules():
    """
    List available modules in the book.
    """
    return {
        "modules": [
            {
                "id": "module-1-ros2",
                "name": "Module 1: ROS 2 - The Robotic Nervous System",
                "description": "ROS 2 fundamentals, nodes, topics, URDF",
                "chapters": 13,
            },
            {
                "id": "module-2-digital-twin",
                "name": "Module 2: Digital Twin - Gazebo & Unity",
                "description": "Physics simulation and visualization",
                "chapters": 13,
            },
            {
                "id": "module-3-isaac",
                "name": "Module 3: AI-Robot Brain - NVIDIA Isaac",
                "description": "Photorealistic simulation and navigation",
                "chapters": 13,
            },
            {
                "id": "module-4-vla",
                "name": "Module 4: Vision-Language-Action",
                "description": "LLM-powered autonomous robots",
                "chapters": 14,
            },
        ]
    }
