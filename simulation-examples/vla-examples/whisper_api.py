"""
Whisper API Integration with Error Handling for VLA Pipeline

This module provides robust integration with OpenAI's Whisper API,
including comprehensive error handling, retry mechanisms, and
fallback strategies for the Vision-Language-Action pipeline.
"""

import asyncio
import aiohttp
import openai
import time
import logging
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import backoff  # For retry logic
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhisperErrorType(Enum):
    """Types of errors that can occur with Whisper API"""
    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    INTERNAL_ERROR = "internal_error"


@dataclass
class WhisperResponse:
    """Response from Whisper API with error handling"""
    text: str
    language: str
    duration: float
    segments: List[Dict[str, Any]]
    error: Optional[str] = None
    error_type: Optional[WhisperErrorType] = None
    confidence: Optional[float] = None
    processing_time: float = 0.0


class WhisperAPIManager:
    """
    Manager class for Whisper API integration with comprehensive error handling
    """

    def __init__(self, api_key: Optional[str] = None, max_retries: int = 3, timeout: int = 30):
        """
        Initialize Whisper API manager

        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY environment variable
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = openai.api_key or openai.api_key_path or openai.load_api_key() or openai.util.default_api_key()
            if not self.api_key:
                self.api_key = openai.api_key = openai.util.get_api_key()

        # Fallback to environment variable
        if not self.api_key:
            import os
            self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OpenAI API key must be provided either as parameter or via OPENAI_API_KEY environment variable")

        openai.api_key = self.api_key
        self.model = "whisper-1"
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = self._create_session()

        logger.info("Whisper API Manager initialized with error handling")

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy"""
        session = requests.Session()

        # Define retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    @backoff.on_exception(backoff.expo, (requests.exceptions.RequestException, openai.error.RateLimitError), max_tries=3)
    async def transcribe_file(self, file_path: str, language: str = "en",
                            response_format: str = "verbose_json") -> WhisperResponse:
        """
        Transcribe audio file using Whisper API with error handling

        Args:
            file_path: Path to the audio file
            language: Language of the audio
            response_format: Format of the response

        Returns:
            WhisperResponse object with transcription or error details
        """
        start_time = time.time()

        try:
            # Validate file exists and is accessible
            if not Path(file_path).exists():
                return WhisperResponse(
                    text="",
                    language=language,
                    duration=0.0,
                    segments=[],
                    error=f"File does not exist: {file_path}",
                    error_type=WhisperErrorType.VALIDATION_ERROR
                )

            # Validate file size (OpenAI has limits)
            file_size = Path(file_path).stat().st_size
            if file_size > 25 * 1024 * 1024:  # 25MB limit
                return WhisperResponse(
                    text="",
                    language=language,
                    duration=0.0,
                    segments=[],
                    error=f"File too large: {file_size} bytes (max 25MB)",
                    error_type=WhisperErrorType.VALIDATION_ERROR
                )

            # Attempt transcription with OpenAI API
            with open(file_path, "rb") as audio_file:
                transcript = await openai.Audio.atranscribe(
                    model=self.model,
                    file=audio_file,
                    language=language,
                    response_format=response_format
                )

            processing_time = time.time() - start_time

            # Calculate confidence based on transcript quality
            confidence = self._calculate_confidence(transcript)

            return WhisperResponse(
                text=transcript.text,
                language=transcript.language,
                duration=transcript.duration,
                segments=getattr(transcript, 'segments', []),
                confidence=confidence,
                processing_time=processing_time
            )

        except openai.error.RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            return WhisperResponse(
                text="",
                language=language,
                duration=0.0,
                segments=[],
                error=f"Rate limit exceeded: {str(e)}",
                error_type=WhisperErrorType.RATE_LIMIT_ERROR
            )

        except openai.error.AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            return WhisperResponse(
                text="",
                language=language,
                duration=0.0,
                segments=[],
                error=f"Authentication failed: {str(e)}",
                error_type=WhisperErrorType.AUTHENTICATION_ERROR
            )

        except openai.error.APIConnectionError as e:
            logger.error(f"API connection error: {e}")
            return WhisperResponse(
                text="",
                language=language,
                duration=0.0,
                segments=[],
                error=f"API connection error: {str(e)}",
                error_type=WhisperErrorType.NETWORK_ERROR
            )

        except openai.error.Timeout as e:
            logger.error(f"API timeout: {e}")
            return WhisperResponse(
                text="",
                language=language,
                duration=0.0,
                segments=[],
                error=f"API timeout: {str(e)}",
                error_type=WhisperErrorType.TIMEOUT_ERROR
            )

        except openai.error.APIError as e:
            logger.error(f"API error: {e}")
            return WhisperResponse(
                text="",
                language=language,
                duration=0.0,
                segments=[],
                error=f"API error: {str(e)}",
                error_type=WhisperErrorType.API_ERROR
            )

        except Exception as e:
            logger.error(f"Unexpected error during transcription: {e}")
            return WhisperResponse(
                text="",
                language=language,
                duration=0.0,
                segments=[],
                error=f"Unexpected error: {str(e)}",
                error_type=WhisperErrorType.INTERNAL_ERROR
            )

    @backoff.on_exception(backoff.expo, (requests.exceptions.RequestException, openai.error.RateLimitError), max_tries=3)
    def transcribe_file_sync(self, file_path: str, language: str = "en",
                           response_format: str = "verbose_json") -> WhisperResponse:
        """
        Synchronous version of transcribe_file with error handling

        Args:
            file_path: Path to the audio file
            language: Language of the audio
            response_format: Format of the response

        Returns:
            WhisperResponse object with transcription or error details
        """
        start_time = time.time()

        try:
            # Validate file exists and is accessible
            if not Path(file_path).exists():
                return WhisperResponse(
                    text="",
                    language=language,
                    duration=0.0,
                    segments=[],
                    error=f"File does not exist: {file_path}",
                    error_type=WhisperErrorType.VALIDATION_ERROR
                )

            # Validate file size (OpenAI has limits)
            file_size = Path(file_path).stat().st_size
            if file_size > 25 * 1024 * 1024:  # 25MB limit
                return WhisperResponse(
                    text="",
                    language=language,
                    duration=0.0,
                    segments=[],
                    error=f"File too large: {file_size} bytes (max 25MB)",
                    error_type=WhisperErrorType.VALIDATION_ERROR
                )

            # Attempt transcription with OpenAI API
            with open(file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe(
                    model=self.model,
                    file=audio_file,
                    language=language,
                    response_format=response_format
                )

            processing_time = time.time() - start_time

            # Calculate confidence based on transcript quality
            confidence = self._calculate_confidence(transcript)

            return WhisperResponse(
                text=transcript.text,
                language=transcript.language,
                duration=transcript.duration,
                segments=getattr(transcript, 'segments', []),
                confidence=confidence,
                processing_time=processing_time
            )

        except openai.error.RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            return WhisperResponse(
                text="",
                language=language,
                duration=0.0,
                segments=[],
                error=f"Rate limit exceeded: {str(e)}",
                error_type=WhisperErrorType.RATE_LIMIT_ERROR
            )

        except openai.error.AuthenticationError as e:
            logger.error(f"Authentication failed: {e}")
            return WhisperResponse(
                text="",
                language=language,
                duration=0.0,
                segments=[],
                error=f"Authentication failed: {str(e)}",
                error_type=WhisperErrorType.AUTHENTICATION_ERROR
            )

        except openai.error.APIConnectionError as e:
            logger.error(f"API connection error: {e}")
            return WhisperResponse(
                text="",
                language=language,
                duration=0.0,
                segments=[],
                error=f"API connection error: {str(e)}",
                error_type=WhisperErrorType.NETWORK_ERROR
            )

        except openai.error.Timeout as e:
            logger.error(f"API timeout: {e}")
            return WhisperResponse(
                text="",
                language=language,
                duration=0.0,
                segments=[],
                error=f"API timeout: {str(e)}",
                error_type=WhisperErrorType.TIMEOUT_ERROR
            )

        except openai.error.APIError as e:
            logger.error(f"API error: {e}")
            return WhisperResponse(
                text="",
                language=language,
                duration=0.0,
                segments=[],
                error=f"API error: {str(e)}",
                error_type=WhisperErrorType.API_ERROR
            )

        except Exception as e:
            logger.error(f"Unexpected error during transcription: {e}")
            return WhisperResponse(
                text="",
                language=language,
                duration=0.0,
                segments=[],
                error=f"Unexpected error: {str(e)}",
                error_type=WhisperErrorType.INTERNAL_ERROR
            )

    def _calculate_confidence(self, transcript) -> float:
        """
        Calculate confidence score for the transcription
        Note: Whisper doesn't directly provide confidence, so we estimate it
        """
        if hasattr(transcript, 'text') and transcript.text:
            text_length = len(transcript.text.strip())
            # Simple heuristic: longer, more detailed transcriptions are more likely to be accurate
            # This is a basic estimation - in practice, you might use more sophisticated methods
            estimated_confidence = min(0.95, max(0.1, 0.5 + (text_length / 1000)))
            return estimated_confidence
        return 0.1

    async def transcribe_with_fallback(self, file_path: str, language: str = "en") -> WhisperResponse:
        """
        Transcribe with fallback mechanisms in case of API failure

        Args:
            file_path: Path to the audio file
            language: Language of the audio

        Returns:
            WhisperResponse object with transcription or error details
        """
        # First, try the main API
        result = await self.transcribe_file(file_path, language)

        # If it fails with a rate limit or network error, we could implement fallback logic
        # For now, just return the result
        if result.error and result.error_type in [WhisperErrorType.RATE_LIMIT_ERROR, WhisperErrorType.NETWORK_ERROR]:
            logger.info("API failed, but no fallback implemented yet")

        return result

    def validate_audio_file(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Validate audio file before sending to API

        Args:
            file_path: Path to the audio file

        Returns:
            Tuple of (is_valid, list_of_validation_errors)
        """
        errors = []

        # Check if file exists
        path = Path(file_path)
        if not path.exists():
            errors.append(f"File does not exist: {file_path}")
            return False, errors

        # Check file size
        file_size = path.stat().st_size
        if file_size > 25 * 1024 * 1024:  # 25MB limit
            errors.append(f"File too large: {file_size} bytes (max 25MB)")

        # Check file extension (basic check)
        valid_extensions = ['.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm']
        if path.suffix.lower() not in valid_extensions:
            errors.append(f"Invalid file format: {path.suffix}. Valid formats: {valid_extensions}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for the Whisper API
        Note: This is a placeholder - actual implementation would depend on OpenAI's billing API
        """
        return {
            "requests_made": 0,
            "total_duration_processed": 0.0,
            "estimated_cost": 0.0,
            "remaining_quota": "unknown"
        }

    def batch_transcribe(self, file_paths: List[str], language: str = "en") -> List[WhisperResponse]:
        """
        Transcribe multiple files in batch

        Args:
            file_paths: List of file paths to transcribe
            language: Language of the audio files

        Returns:
            List of WhisperResponse objects
        """
        results = []

        for file_path in file_paths:
            is_valid, validation_errors = self.validate_audio_file(file_path)

            if not is_valid:
                result = WhisperResponse(
                    text="",
                    language=language,
                    duration=0.0,
                    segments=[],
                    error=f"Validation failed: {', '.join(validation_errors)}",
                    error_type=WhisperErrorType.VALIDATION_ERROR
                )
                results.append(result)
                continue

            # For batch processing, use the synchronous method to avoid overwhelming the API
            result = self.transcribe_file_sync(file_path, language)
            results.append(result)

        return results


class WhisperFallbackHandler:
    """
    Handler for managing fallback options when Whisper API is unavailable
    """

    def __init__(self):
        self.fallback_options = []
        self.enabled = True

    def add_fallback_option(self, name: str, function):
        """Add a fallback transcription option"""
        self.fallback_options.append({
            'name': name,
            'function': function
        })

    def execute_fallback(self, file_path: str, language: str = "en") -> Optional[WhisperResponse]:
        """Execute fallback transcription if available"""
        if not self.enabled or not self.fallback_options:
            return None

        # For now, return a placeholder response
        # In a real implementation, this would call alternative transcription services
        return WhisperResponse(
            text="Fallback transcription not implemented",
            language=language,
            duration=0.0,
            segments=[],
            error="Using fallback transcription",
            error_type=WhisperErrorType.API_ERROR
        )


def main():
    """Example usage of the Whisper API integration with error handling"""
    print("Whisper API Integration with Error Handling Example")

    try:
        # Initialize Whisper API manager
        whisper_manager = WhisperAPIManager()

        # Example: Validate an audio file
        print("\n--- File Validation Example ---")
        is_valid, errors = whisper_manager.validate_audio_file("example_audio.mp3")
        print(f"File validation result: Valid={is_valid}")
        if errors:
            print(f"Validation errors: {errors}")

        # Example: Get usage stats
        print("\n--- Usage Stats Example ---")
        stats = whisper_manager.get_usage_stats()
        print(f"Usage stats: {stats}")

        # Example: Batch transcription (with simulated files)
        print("\n--- Batch Transcription Example ---")
        # Note: This would require actual audio files to work
        # For demo purposes, we'll just show the structure
        print("Batch transcription would process multiple files...")

        # Example: Error handling demonstration
        print("\n--- Error Handling Example ---")
        # This would show how errors are handled in real usage
        print("Error handling would catch and manage API issues...")

        print("\nWhisper API integration example completed!")

    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please ensure OPENAI_API_KEY environment variable is set")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()