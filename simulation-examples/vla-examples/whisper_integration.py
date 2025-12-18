"""
Whisper Integration Module for VLA Pipeline

This module provides integration with OpenAI's Whisper API for
voice-to-text conversion in the Vision-Language-Action pipeline.
"""

import asyncio
import base64
import io
import os
import time
import wave
from typing import Dict, List, Optional, Tuple, Any
import openai
import numpy as np
import sounddevice as sd
import pydub
from pydub import AudioSegment
import requests
import aiohttp
from dataclasses import dataclass
from pathlib import Path

@dataclass
class VoiceCommand:
    """Represents a processed voice command"""
    text: str
    confidence: float
    timestamp: float
    audio_duration: float
    language: str = "en"
    raw_audio_data: Optional[bytes] = None

class WhisperIntegration:
    """
    Integration class for OpenAI Whisper API
    Handles voice recording, processing, and conversion to text
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Whisper integration

        Args:
            api_key: OpenAI API key. If None, will use OPENAI_API_KEY environment variable
        """
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY environment variable must be set")

        openai.api_key = self.api_key
        self.model = "whisper-1"

        # Audio recording parameters
        self.sample_rate = 16000  # Hz
        self.channels = 1
        self.dtype = np.int16
        self.chunk_duration = 1.0  # seconds
        self.silence_threshold = 0.01  # amplitude threshold for silence detection

        # Recording state
        self.is_recording = False
        self.audio_buffer = []

        print("Whisper integration initialized")

    async def record_audio_async(self, duration: float = 5.0) -> np.ndarray:
        """
        Record audio asynchronously for specified duration

        Args:
            duration: Recording duration in seconds

        Returns:
            Numpy array containing the recorded audio samples
        """
        print(f"Recording audio for {duration} seconds...")

        # Record audio
        audio_data = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype
        )
        sd.wait()  # Wait for recording to complete

        print("Recording completed")
        return audio_data.flatten()

    def record_audio(self, duration: float = 5.0) -> np.ndarray:
        """
        Record audio synchronously for specified duration

        Args:
            duration: Recording duration in seconds

        Returns:
            Numpy array containing the recorded audio samples
        """
        print(f"Recording audio for {duration} seconds...")

        # Record audio
        audio_data = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype
        )
        sd.wait()  # Wait for recording to complete

        print("Recording completed")
        return audio_data.flatten()

    def save_audio_to_wav(self, audio_data: np.ndarray, filepath: str) -> None:
        """
        Save audio data to WAV file

        Args:
            audio_data: Numpy array containing audio samples
            filepath: Path to save the WAV file
        """
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        print(f"Audio saved to {filepath}")

    def audio_to_wav_bytes(self, audio_data: np.ndarray) -> bytes:
        """
        Convert audio data to WAV bytes for API upload

        Args:
            audio_data: Numpy array containing audio samples

        Returns:
            Bytes of WAV-encoded audio data
        """
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        return buffer.getvalue()

    async def transcribe_audio_async(self, audio_data: np.ndarray, language: str = "en") -> VoiceCommand:
        """
        Transcribe audio to text using OpenAI Whisper API (async)

        Args:
            audio_data: Numpy array containing audio samples
            language: Language of the audio (default: "en")

        Returns:
            VoiceCommand object with transcription and metadata
        """
        start_time = time.time()

        # Convert audio data to WAV bytes
        wav_bytes = self.audio_to_wav_bytes(audio_data)

        # Create a temporary file for the API
        temp_file = "temp_audio.wav"
        with open(temp_file, "wb") as f:
            f.write(wav_bytes)

        try:
            # Transcribe using Whisper API
            with open(temp_file, "rb") as audio_file:
                transcript = await openai.Audio.atranscribe(
                    model=self.model,
                    file=audio_file,
                    language=language,
                    response_format="verbose_json"
                )

            # Calculate confidence based on various factors
            # Note: Whisper API doesn't directly return confidence, so we estimate it
            text_length = len(transcript.text.strip())
            audio_duration = len(audio_data) / self.sample_rate
            estimated_confidence = min(0.95, max(0.1, 0.5 + (text_length / (audio_duration * 10))))

            voice_command = VoiceCommand(
                text=transcript.text,
                confidence=estimated_confidence,
                timestamp=time.time(),
                audio_duration=audio_duration,
                language=language,
                raw_audio_data=wav_bytes
            )

            print(f"Transcription: '{transcript.text}' (confidence: {estimated_confidence:.2f})")
            return voice_command

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def transcribe_audio(self, audio_data: np.ndarray, language: str = "en") -> VoiceCommand:
        """
        Transcribe audio to text using OpenAI Whisper API (sync)

        Args:
            audio_data: Numpy array containing audio samples
            language: Language of the audio (default: "en")

        Returns:
            VoiceCommand object with transcription and metadata
        """
        start_time = time.time()

        # Convert audio data to WAV bytes
        wav_bytes = self.audio_to_wav_bytes(audio_data)

        # Create a temporary file for the API
        temp_file = "temp_audio.wav"
        with open(temp_file, "wb") as f:
            f.write(wav_bytes)

        try:
            # Transcribe using Whisper API
            with open(temp_file, "rb") as audio_file:
                transcript = openai.Audio.transcribe(
                    model=self.model,
                    file=audio_file,
                    language=language,
                    response_format="verbose_json"
                )

            # Calculate confidence based on various factors
            # Note: Whisper API doesn't directly return confidence, so we estimate it
            text_length = len(transcript.text.strip())
            audio_duration = len(audio_data) / self.sample_rate
            estimated_confidence = min(0.95, max(0.1, 0.5 + (text_length / (audio_duration * 10))))

            voice_command = VoiceCommand(
                text=transcript.text,
                confidence=estimated_confidence,
                timestamp=time.time(),
                audio_duration=audio_duration,
                language=language,
                raw_audio_data=wav_bytes
            )

            print(f"Transcription: '{transcript.text}' (confidence: {estimated_confidence:.2f})")
            return voice_command

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def detect_silence(self, audio_data: np.ndarray, threshold: float = None) -> bool:
        """
        Detect if the audio contains silence based on amplitude threshold

        Args:
            audio_data: Numpy array containing audio samples
            threshold: Amplitude threshold for silence detection

        Returns:
            True if silence is detected, False otherwise
        """
        if threshold is None:
            threshold = self.silence_threshold

        # Calculate RMS amplitude
        rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
        return rms < threshold

    async def continuous_listen(self, callback_func, timeout: float = 60.0, silence_duration: float = 2.0):
        """
        Continuously listen for voice commands and process them

        Args:
            callback_func: Function to call with each processed VoiceCommand
            timeout: Maximum listening time in seconds
            silence_duration: Duration of silence to detect end of command
        """
        print(f"Starting continuous listening (timeout: {timeout}s)...")

        start_time = time.time()
        listening_for_command = False
        silence_start_time = None

        while time.time() - start_time < timeout:
            # Record a chunk of audio
            chunk = self.record_audio(duration=self.chunk_duration)

            # Check if we're listening for a command
            if not listening_for_command:
                # Check if this chunk contains speech (not silence)
                if not self.detect_silence(chunk):
                    print("Speech detected, starting command recording...")
                    listening_for_command = True
                    full_command_audio = chunk.copy()
                    silence_start_time = None
            else:
                # We're in a command, continue recording
                full_command_audio = np.concatenate([full_command_audio, chunk])

                # Check if we have silence (end of command)
                if self.detect_silence(chunk):
                    if silence_start_time is None:
                        silence_start_time = time.time()
                    elif time.time() - silence_start_time >= silence_duration:
                        # End of command detected
                        print("Command end detected, processing...")
                        try:
                            voice_command = await self.transcribe_audio_async(full_command_audio)
                            if voice_command.confidence > 0.3:  # Only process confident transcriptions
                                await callback_func(voice_command)
                        except Exception as e:
                            print(f"Error processing command: {e}")

                        # Reset for next command
                        listening_for_command = False
                        silence_start_time = None
                else:
                    # Reset silence timer if we hear speech
                    silence_start_time = None

        print("Continuous listening ended")

    def validate_voice_command(self, voice_command: VoiceCommand, min_confidence: float = 0.5) -> bool:
        """
        Validate a voice command based on confidence and content

        Args:
            voice_command: VoiceCommand to validate
            min_confidence: Minimum confidence threshold

        Returns:
            True if command is valid, False otherwise
        """
        if voice_command.confidence < min_confidence:
            print(f"Command rejected: confidence {voice_command.confidence:.2f} below threshold {min_confidence}")
            return False

        if not voice_command.text.strip():
            print("Command rejected: empty text")
            return False

        # Additional validation could include:
        # - Checking for robot-related keywords
        # - Validating command structure
        # - Checking for safety concerns

        return True

    def preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Preprocess audio data to improve transcription quality

        Args:
            audio_data: Raw audio data

        Returns:
            Preprocessed audio data
        """
        # Convert to AudioSegment for processing
        audio_segment = AudioSegment(
            data=audio_data.tobytes(),
            sample_width=2,  # 16-bit
            frame_rate=self.sample_rate,
            channels=self.channels
        )

        # Apply audio processing
        # Normalize audio
        audio_segment = audio_segment.normalize()

        # Apply noise reduction (simple approach)
        # In a real implementation, you might use more sophisticated noise reduction
        audio_segment = audio_segment.apply_gain(-audio_segment.dBFS + -20.0)  # Normalize to -20dB

        # Convert back to numpy array
        processed_audio = np.frombuffer(audio_segment.raw_data, dtype=np.int16)

        return processed_audio


class VLAWhisperNode:
    """
    ROS 2 node wrapper for Whisper integration
    """

    def __init__(self):
        self.whisper = WhisperIntegration()
        self.command_history: List[VoiceCommand] = []

    async def process_voice_command(self, voice_command: VoiceCommand) -> Dict[str, Any]:
        """
        Process a voice command and return structured response
        This would typically interface with the VLA pipeline
        """
        result = {
            "command": voice_command.text,
            "confidence": voice_command.confidence,
            "timestamp": voice_command.timestamp,
            "processed": True,
            "intent": self.extract_intent(voice_command.text),
            "entities": self.extract_entities(voice_command.text)
        }

        # Add to history
        self.command_history.append(voice_command)

        return result

    def extract_intent(self, text: str) -> str:
        """
        Simple intent extraction (in a real system, this would use NLP)
        """
        text_lower = text.lower()

        if any(word in text_lower for word in ["move", "go", "navigate", "walk", "drive"]):
            return "navigation"
        elif any(word in text_lower for word in ["pick", "grasp", "take", "grab", "lift", "place", "put"]):
            return "manipulation"
        elif any(word in text_lower for word in ["look", "see", "find", "detect", "identify"]):
            return "perception"
        elif any(word in text_lower for word in ["stop", "halt", "pause", "wait"]):
            return "stop"
        else:
            return "unknown"

    def extract_entities(self, text: str) -> List[str]:
        """
        Simple entity extraction (in a real system, this would use NLP)
        """
        # This is a very basic implementation
        # In reality, you'd use NER (Named Entity Recognition)
        entities = []

        # Common object types in robotics context
        object_types = ["cup", "bottle", "box", "chair", "table", "door", "window", "person"]

        text_lower = text.lower()
        for obj_type in object_types:
            if obj_type in text_lower:
                entities.append(obj_type)

        return entities


# Example usage and testing functions
async def example_voice_callback(voice_command: VoiceCommand):
    """Example callback function for processing voice commands"""
    print(f"Received command: '{voice_command.text}' with confidence {voice_command.confidence:.2f}")

    # Create a VLA node and process the command
    vla_node = VLAWhisperNode()
    result = await vla_node.process_voice_command(voice_command)

    print(f"Processed result: {result}")


def main():
    """Example main function demonstrating Whisper integration"""
    print("VLA Whisper Integration Example")

    # Initialize Whisper integration
    # Note: This requires OPENAI_API_KEY to be set in environment
    try:
        whisper = WhisperIntegration()

        # Example 1: Simple recording and transcription
        print("\n--- Example 1: Simple Recording ---")
        audio_data = whisper.record_audio(duration=3.0)
        voice_command = whisper.transcribe_audio(audio_data)

        if whisper.validate_voice_command(voice_command):
            print(f"Valid command received: {voice_command.text}")
        else:
            print("Command did not pass validation")

        # Example 2: Audio preprocessing
        print("\n--- Example 2: Audio Preprocessing ---")
        processed_audio = whisper.preprocess_audio(audio_data)
        processed_command = whisper.transcribe_audio(processed_audio)
        print(f"Preprocessed result: {processed_command.text}")

        # Example 3: Continuous listening (would normally run continuously)
        print("\n--- Example 3: Continuous Listening Simulation ---")
        # For demo purposes, we'll just show the structure
        print("Continuous listening would start here...")
        print("It would listen for commands and process them using the callback")

    except ValueError as e:
        print(f"Error: {e}")
        print("Please set OPENAI_API_KEY environment variable")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()