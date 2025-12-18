"""
OpenAI Agent service for RAG-powered chat.
Implements chain-of-thought reasoning with grounded responses.
"""

from typing import List, Optional, AsyncIterator
import logging
from datetime import datetime

from openai import AsyncOpenAI

from ..config import get_settings
from ..models import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    MessageRole,
    Citation,
    SearchResult,
)
from .retrieval import get_retrieval_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert AI assistant for the "Physical AI & Humanoid Robotics" textbook. Your role is to help students learn about:

1. **ROS 2** - The Robot Operating System middleware
2. **Digital Twins** - Gazebo and Unity simulation
3. **NVIDIA Isaac** - Photorealistic simulation and perception
4. **Vision-Language-Action (VLA)** - LLM-powered autonomous robots

## Guidelines:

1. **Be accurate**: Only answer based on the provided context from the book. If information isn't in the context, say so clearly.

2. **Be educational**: Explain concepts clearly, provide examples, and relate to practical robotics applications.

3. **Cite sources**: Reference specific chapters when providing information.

4. **Code examples**: When relevant, provide working code snippets in Python (ROS 2), YAML, or XML (URDF).

5. **Stay focused**: Keep answers relevant to robotics, ROS 2, simulation, and AI. Redirect off-topic questions back to the book content.

6. **Safety first**: Always emphasize safety considerations when discussing robot control or manipulation.

## Response Format:

- Start with a direct answer to the question
- Provide supporting details from the book
- Include code examples if helpful
- End with a suggestion for related topics to explore

If the user's question cannot be answered from the provided context, politely explain what you can help with instead."""


class AgentService:
    """OpenAI-powered agent for RAG chat."""

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.retrieval_service = get_retrieval_service()

    async def chat(
        self,
        request: ChatRequest,
        chat_history: List[ChatMessage] = None,
    ) -> ChatResponse:
        """Process a chat request with RAG.

        Args:
            request: Chat request from user
            chat_history: Previous messages in the conversation

        Returns:
            Chat response with citations
        """
        start_time = datetime.utcnow()

        # Retrieve relevant context
        results, citations = await self.retrieval_service.retrieve_context(
            query=request.message,
            top_k=request.max_context_chunks,
            module_filter=request.module_filter,
        )

        # Build context prompt
        context = self.retrieval_service.build_context_prompt(results)

        # Build messages for OpenAI
        messages = self._build_messages(
            user_message=request.message,
            context=context,
            chat_history=chat_history or [],
        )

        # Call OpenAI
        response = await self.client.chat.completions.create(
            model=self.settings.openai_chat_model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=2000,
        )

        # Extract response
        assistant_content = response.choices[0].message.content

        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000

        # Build response
        assistant_message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            citations=citations if request.include_citations else [],
        )

        return ChatResponse(
            message=assistant_message,
            session_id=request.session_id or "new_session",
            context_chunks_used=len(results),
            total_tokens_used=response.usage.total_tokens,
            processing_time_ms=processing_time,
        )

    async def stream_chat(
        self,
        request: ChatRequest,
        chat_history: List[ChatMessage] = None,
    ) -> AsyncIterator[str]:
        """Stream chat response for real-time output.

        Args:
            request: Chat request
            chat_history: Previous messages

        Yields:
            Response chunks as they're generated
        """
        # Retrieve context
        results, _ = await self.retrieval_service.retrieve_context(
            query=request.message,
            top_k=request.max_context_chunks,
            module_filter=request.module_filter,
        )

        context = self.retrieval_service.build_context_prompt(results)

        messages = self._build_messages(
            user_message=request.message,
            context=context,
            chat_history=chat_history or [],
        )

        # Stream response
        stream = await self.client.chat.completions.create(
            model=self.settings.openai_chat_model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=2000,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _build_messages(
        self,
        user_message: str,
        context: str,
        chat_history: List[ChatMessage],
    ) -> List[dict]:
        """Build message list for OpenAI API.

        Args:
            user_message: Current user message
            context: Retrieved context
            chat_history: Previous conversation messages

        Returns:
            List of message dicts for OpenAI
        """
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add chat history (limit to last 10 messages)
        for msg in chat_history[-10:]:
            messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })

        # Add context and user message
        user_content = f"""## Relevant Context from the Book:

{context if context else "No specific context found for this question."}

## User Question:

{user_message}

Please answer based on the context provided. If the information isn't in the context, say so."""

        messages.append({"role": "user", "content": user_content})

        return messages

    async def suggest_topics(
        self,
        message: str,
        n_suggestions: int = 3,
    ) -> List[str]:
        """Suggest related topics based on user message.

        Args:
            message: User's message
            n_suggestions: Number of suggestions

        Returns:
            List of suggested topics
        """
        prompt = f"""Based on this robotics question: "{message}"

Suggest {n_suggestions} related topics from these areas that the user might want to explore:
- ROS 2 fundamentals (nodes, topics, services, URDF)
- Gazebo simulation
- Unity for robotics
- NVIDIA Isaac Sim
- Navigation (Nav2, SLAM)
- Vision-Language-Action (VLA) systems

Return only topic names, one per line, no explanations."""

        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",  # Use smaller model for suggestions
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200,
        )

        suggestions = response.choices[0].message.content.strip().split("\n")
        return [s.strip("- ").strip() for s in suggestions[:n_suggestions]]


# Singleton instance
_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """Get or create agent service instance."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
