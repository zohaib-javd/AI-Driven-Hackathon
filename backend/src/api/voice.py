"""
Voice API endpoints for Whisper speech-to-text integration.
Enables voice commands for the Physical AI chatbot.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import logging
import tempfile
import os
from pathlib import Path

from openai import AsyncOpenAI

from ..config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])


class TranscriptionResponse(BaseModel):
    """Response from transcription endpoint."""
    text: str
    language: str
    duration: Optional[float] = None
    confidence: Optional[float] = None


class VoiceCommandResponse(BaseModel):
    """Response from voice command processing."""
    transcription: str
    intent: str
    response: str


# Supported audio formats for Whisper
SUPPORTED_FORMATS = {'.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm'}


async def transcribe_audio(audio_file: UploadFile) -> str:
    """
    Transcribe audio file using OpenAI Whisper API.

    Args:
        audio_file: Uploaded audio file

    Returns:
        Transcribed text
    """
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Validate file extension
    filename = audio_file.filename or "audio.wav"
    ext = Path(filename).suffix.lower()

    if ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {ext}. Supported: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Save to temporary file (Whisper API requires a file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        content = await audio_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Call Whisper API
        with open(tmp_path, "rb") as audio:
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                response_format="text"
            )

        return transcription.strip()

    finally:
        # Clean up temp file
        os.unlink(tmp_path)


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_endpoint(
    file: UploadFile = File(..., description="Audio file to transcribe")
):
    """
    Transcribe audio to text using Whisper.

    Supports: mp3, mp4, mpeg, mpga, m4a, wav, webm

    Returns the transcribed text that can be used as a chat query.
    """
    try:
        text = await transcribe_audio(file)

        # Detect language (simplified - Whisper can return this)
        language = "en"  # Default

        return TranscriptionResponse(
            text=text,
            language=language,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/command", response_model=VoiceCommandResponse)
async def voice_command_endpoint(
    file: UploadFile = File(..., description="Audio file with voice command")
):
    """
    Process a voice command: transcribe and respond.

    1. Transcribes the audio using Whisper
    2. Processes the text as a chat query
    3. Returns both transcription and response

    This is a convenience endpoint that combines transcription
    with chat in a single call.
    """
    try:
        # Transcribe audio
        transcription = await transcribe_audio(file)

        if not transcription:
            return VoiceCommandResponse(
                transcription="",
                intent="unclear",
                response="I couldn't understand the audio. Please try again."
            )

        # Process as chat query
        from .chat import chat
        from ..models import ChatRequest

        chat_request = ChatRequest(
            message=transcription,
            include_citations=True,
            max_context_chunks=5,
            temperature=0.7,
        )

        chat_response = await chat(chat_request)

        # Detect intent (simple heuristics)
        intent = detect_intent(transcription)

        return VoiceCommandResponse(
            transcription=transcription,
            intent=intent,
            response=chat_response.message.content
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice command error: {e}")
        raise HTTPException(status_code=500, detail=f"Voice command failed: {str(e)}")


def detect_intent(text: str) -> str:
    """
    Simple intent detection for voice commands.

    Args:
        text: Transcribed text

    Returns:
        Detected intent category
    """
    text_lower = text.lower()

    # Navigation commands
    if any(word in text_lower for word in ['navigate', 'go to', 'move to', 'take me']):
        return 'navigation'

    # Learning queries
    if any(word in text_lower for word in ['what is', 'how do', 'explain', 'tell me about']):
        return 'learn'

    # Code examples
    if any(word in text_lower for word in ['code', 'example', 'show me', 'write']):
        return 'code'

    # Module specific
    if 'ros' in text_lower or 'robot operating system' in text_lower:
        return 'ros2'
    if 'gazebo' in text_lower or 'simulation' in text_lower:
        return 'simulation'
    if 'isaac' in text_lower or 'nvidia' in text_lower:
        return 'isaac'
    if 'vla' in text_lower or 'voice' in text_lower or 'language' in text_lower:
        return 'vla'

    return 'general'


@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported audio formats."""
    return {
        "formats": list(SUPPORTED_FORMATS),
        "max_size_mb": 25,  # Whisper API limit
        "recommendation": "wav or mp3 for best results"
    }
