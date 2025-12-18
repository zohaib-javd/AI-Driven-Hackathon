"""
Voice Command Preprocessing Pipeline for VLA

This module provides preprocessing for voice commands before they are
sent to the LLM for cognitive planning. It includes noise reduction,
normalization, and command structuring.
"""

import numpy as np
import sounddevice as sd
import pydub
from pydub import AudioSegment
from pydub.effects import normalize
import asyncio
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from scipy import signal
from scipy.signal import butter, filtfilt
import webrtcvad  # WebRTC Voice Activity Detection

@dataclass
class PreprocessedVoiceData:
    """Represents preprocessed voice data"""
    raw_audio: np.ndarray
    processed_audio: np.ndarray
    text_transcription: str
    confidence: float
    preprocessed_text: str
    command_structure: Dict[str, Any]
    timestamp: float
    duration: float

class VoicePreprocessor:
    """
    Preprocessing pipeline for voice commands in the VLA system
    Handles audio preprocessing, text normalization, and command structuring
    """

    def __init__(self):
        self.sample_rate = 16000  # Hz
        self.channels = 1
        self.dtype = np.int16
        self.frame_duration = 0.03  # 30ms frames for VAD
        self.noise_floor = 0.001
        self.speech_threshold = 0.01

        # Initialize WebRTC VAD
        self.vad = webrtcvad.Vad()
        # Set aggressiveness mode (0-3, 3 is most aggressive)
        self.vad.set_mode(2)

        # Initialize audio processing filters
        self._init_filters()

        print("Voice preprocessor initialized")

    def _init_filters(self):
        """Initialize audio processing filters"""
        # High-pass filter to remove DC offset and low-frequency noise
        nyquist = self.sample_rate / 2
        cutoff_freq = 100  # Hz
        self.b_high, self.a_high = butter(4, cutoff_freq / nyquist, btype='high')

        # Low-pass filter to remove high-frequency noise
        cutoff_freq = 7000  # Hz
        self.b_low, self.a_low = butter(4, cutoff_freq / nyquist, btype='low')

    def preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply preprocessing to raw audio data

        Args:
            audio_data: Raw audio data as numpy array

        Returns:
            Preprocessed audio data
        """
        # Convert to float for processing
        audio_float = audio_data.astype(np.float32) / np.iinfo(np.int16).max

        # Apply high-pass filter to remove DC offset
        audio_filtered = filtfilt(self.b_high, self.a_high, audio_float)

        # Apply low-pass filter to remove high-frequency noise
        audio_filtered = filtfilt(self.b_low, self.a_low, audio_filtered)

        # Normalize audio
        audio_normalized = normalize_audio(audio_filtered)

        # Convert back to int16
        audio_processed = (audio_normalized * np.iinfo(np.int16).max).astype(np.int16)

        return audio_processed

    def detect_voice_activity(self, audio_data: np.ndarray) -> List[bool]:
        """
        Detect voice activity in audio frames using WebRTC VAD

        Args:
            audio_data: Audio data as numpy array

        Returns:
            List of booleans indicating voice activity for each frame
        """
        # Convert to the format expected by WebRTC VAD
        # VAD expects 16-bit PCM audio at specific sample rates (8000, 16000, 32000, 48000)
        # and specific frame sizes (10, 20, or 30 ms)

        # Calculate frame size based on sample rate and desired frame duration
        frame_size = int(self.sample_rate * self.frame_duration)
        frames = []

        # Split audio into frames
        for i in range(0, len(audio_data), frame_size):
            frame = audio_data[i:i + frame_size]
            # Pad frame if it's too short
            if len(frame) < frame_size:
                frame = np.pad(frame, (0, frame_size - len(frame)), mode='constant')
            frames.append(frame)

        # Process each frame
        vad_results = []
        for frame in frames:
            # Convert to bytes for WebRTC VAD
            frame_bytes = frame.tobytes()
            try:
                is_speech = self.vad.is_speech(frame_bytes, self.sample_rate)
                vad_results.append(is_speech)
            except Exception:
                # If frame is invalid, assume no speech
                vad_results.append(False)

        return vad_results

    def remove_silence(self, audio_data: np.ndarray, silence_threshold: float = 0.01) -> np.ndarray:
        """
        Remove leading and trailing silence from audio

        Args:
            audio_data: Audio data as numpy array
            silence_threshold: Threshold for silence detection

        Returns:
            Audio data with silence removed
        """
        audio_float = audio_data.astype(np.float32) / np.iinfo(np.int16).max

        # Find non-silent parts of the audio
        non_silent_indices = np.where(np.abs(audio_float) > silence_threshold)[0]

        if len(non_silent_indices) == 0:
            # If all audio is silent, return original
            return audio_data

        # Find start and end of non-silent audio
        start_idx = non_silent_indices[0]
        end_idx = non_silent_indices[-1] + 1

        # Extract non-silent portion
        trimmed_audio = audio_float[start_idx:end_idx]

        # Convert back to int16
        trimmed_audio = (trimmed_audio * np.iinfo(np.int16).max).astype(np.int16)

        return trimmed_audio

    def enhance_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Enhance audio quality by applying various enhancement techniques

        Args:
            audio_data: Audio data as numpy array

        Returns:
            Enhanced audio data
        """
        # Convert to AudioSegment for processing
        audio_segment = AudioSegment(
            data=audio_data.tobytes(),
            sample_width=2,  # 16-bit
            frame_rate=self.sample_rate,
            channels=self.channels
        )

        # Apply normalization
        audio_segment = normalize(audio_segment)

        # Apply noise reduction (simple approach)
        audio_segment = audio_segment.apply_gain(-audio_segment.dBFS + -20.0)  # Normalize to -20dB

        # Convert back to numpy array
        enhanced_audio = np.frombuffer(audio_segment.raw_data, dtype=np.int16)

        return enhanced_audio

    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text transcription to normalize and clean

        Args:
            text: Raw text transcription

        Returns:
            Preprocessed text
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Normalize common robot command terms
        text = self._normalize_robot_commands(text)

        # Remove punctuation that might interfere with command parsing
        text = re.sub(r'[^\w\s]', ' ', text)

        # Remove extra spaces again after punctuation removal
        text = ' '.join(text.split())

        return text

    def _normalize_robot_commands(self, text: str) -> str:
        """
        Normalize common robot command expressions

        Args:
            text: Input text

        Returns:
            Normalized text
        """
        # Dictionary of common variations that should be normalized
        command_mappings = {
            # Navigation commands
            r'\bgo to\b': 'navigate to',
            r'\bmove to\b': 'navigate to',
            r'\bwalk to\b': 'navigate to',
            r'\bgo\b': 'navigate to',
            r'\bmove\b': 'navigate to',
            r'\bwalk\b': 'navigate to',
            r'\bbring me\b': 'fetch',
            r'\bget me\b': 'fetch',
            r'\bgive me\b': 'fetch',
            r'\bpick up\b': 'grasp',
            r'\bgrab\b': 'grasp',
            r'\btake\b': 'grasp',
            r'\bput down\b': 'place',
            r'\bset down\b': 'place',
            r'\bplace\b': 'place',
            r'\bstop\b': 'halt',
            r'\bwait\b': 'pause',
            r'\blook at\b': 'perceive',
            r'\bsee\b': 'perceive',
            r'\bfind\b': 'perceive',

            # Number words to digits
            r'\bone\b': '1',
            r'\btwo\b': '2',
            r'\bthree\b': '3',
            r'\bfour\b': '4',
            r'\bfive\b': '5',
            r'\bsix\b': '6',
            r'\bseven\b': '7',
            r'\beight\b': '8',
            r'\bnine\b': '9',
            r'\bten\b': '10',
        }

        # Apply mappings
        for pattern, replacement in command_mappings.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    def structure_command(self, text: str) -> Dict[str, Any]:
        """
        Structure the command into a more formal representation

        Args:
            text: Preprocessed text command

        Returns:
            Structured command representation
        """
        # Define command patterns
        patterns = {
            'navigation': [
                r'navigate to (.+)',
                r'go to (.+)',
                r'move to (.+)',
                r'walk to (.+)',
                r'go (.+)',
                r'move (.+)'
            ],
            'manipulation': [
                r'grasp (.+)',
                r'pick up (.+)',
                r'grab (.+)',
                r'take (.+)',
                r'place (.+)',
                r'put (.+)',
                r'set (.+)'
            ],
            'perception': [
                r'perceive (.+)',
                r'see (.+)',
                r'find (.+)',
                r'look at (.+)',
                r'detect (.+)'
            ],
            'control': [
                r'stop',
                r'halt',
                r'pause',
                r'wait',
                r'continue'
            ]
        }

        structured_command = {
            'type': 'unknown',
            'action': '',
            'target': '',
            'parameters': {},
            'confidence': 0.0
        }

        text_lower = text.lower()

        # Try to match each pattern
        for cmd_type, cmd_patterns in patterns.items():
            for pattern in cmd_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    structured_command['type'] = cmd_type
                    structured_command['action'] = pattern.split()[0] if ' ' in pattern else pattern
                    if match.groups():
                        structured_command['target'] = match.group(1).strip()
                    structured_command['confidence'] = 0.9  # High confidence for matched patterns
                    break
            if structured_command['type'] != 'unknown':
                break

        # If no pattern matched, use the full text as target with unknown type
        if structured_command['type'] == 'unknown':
            structured_command['target'] = text
            structured_command['confidence'] = 0.3  # Lower confidence for unmatched commands

        return structured_command

    def preprocess_voice_data(self, audio_data: np.ndarray, text_transcription: str, confidence: float) -> PreprocessedVoiceData:
        """
        Complete preprocessing pipeline for voice data

        Args:
            audio_data: Raw audio data
            text_transcription: Text transcription of the audio
            confidence: Confidence of the transcription

        Returns:
            PreprocessedVoiceData object with all preprocessing results
        """
        import time

        start_time = time.time()

        # Preprocess audio
        processed_audio = self.preprocess_audio(audio_data)

        # Preprocess text
        preprocessed_text = self.preprocess_text(text_transcription)

        # Structure command
        command_structure = self.structure_command(preprocessed_text)

        # Calculate duration
        duration = len(audio_data) / self.sample_rate

        result = PreprocessedVoiceData(
            raw_audio=audio_data,
            processed_audio=processed_audio,
            text_transcription=text_transcription,
            confidence=confidence,
            preprocessed_text=preprocessed_text,
            command_structure=command_structure,
            timestamp=time.time(),
            duration=duration
        )

        print(f"Voice preprocessing completed in {time.time() - start_time:.3f}s")
        return result

    def batch_preprocess(self, audio_segments: List[np.ndarray], transcriptions: List[str], confidences: List[float]) -> List[PreprocessedVoiceData]:
        """
        Preprocess a batch of voice data segments

        Args:
            audio_segments: List of audio data segments
            transcriptions: List of text transcriptions
            confidences: List of confidence scores

        Returns:
            List of PreprocessedVoiceData objects
        """
        results = []
        for audio, text, conf in zip(audio_segments, transcriptions, confidences):
            result = self.preprocess_voice_data(audio, text, conf)
            results.append(result)

        return results


class VoiceCommandValidator:
    """
    Validator for voice commands to ensure they are appropriate for the VLA system
    """

    def __init__(self):
        self.min_confidence = 0.5
        self.max_command_length = 200  # characters
        self.max_processing_time = 5.0  # seconds

        # Define allowed command patterns
        self.allowed_patterns = [
            r'navigate to .+',
            r'grasp .+',
            r'pick up .+',
            r'place .+',
            r'perceive .+',
            r'find .+',
            r'stop',
            r'pause',
            r'continue',
        ]

        # Define forbidden words/phrases
        self.forbidden_patterns = [
            r'shutdown',
            r'reboot',
            r'reset',
            r'factory reset',
            r'format',
            r'delete',
        ]

    def validate_command(self, preprocessed_data: PreprocessedVoiceData) -> Tuple[bool, List[str]]:
        """
        Validate a preprocessed voice command

        Args:
            preprocessed_data: Preprocessed voice data to validate

        Returns:
            Tuple of (is_valid, list_of_validation_errors)
        """
        errors = []

        # Check confidence
        if preprocessed_data.confidence < self.min_confidence:
            errors.append(f"Confidence {preprocessed_data.confidence:.2f} below minimum {self.min_confidence}")

        # Check command length
        if len(preprocessed_data.preprocessed_text) > self.max_command_length:
            errors.append(f"Command too long: {len(preprocessed_data.preprocessed_text)} chars > {self.max_command_length}")

        # Check for forbidden patterns
        text_lower = preprocessed_data.preprocessed_text.lower()
        for pattern in self.forbidden_patterns:
            if re.search(pattern, text_lower):
                errors.append(f"Forbidden command pattern detected: {pattern}")

        # Check if command matches allowed patterns (optional - for strict validation)
        # For now, we'll allow all commands but could be more restrictive
        # matched_allowed = any(re.match(pattern, text_lower) for pattern in self.allowed_patterns)
        # if not matched_allowed:
        #     errors.append("Command does not match any allowed pattern")

        is_valid = len(errors) == 0
        return is_valid, errors

    def sanitize_command(self, preprocessed_data: PreprocessedVoiceData) -> PreprocessedVoiceData:
        """
        Sanitize command by removing potentially harmful elements

        Args:
            preprocessed_data: Preprocessed voice data to sanitize

        Returns:
            Sanitized PreprocessedVoiceData
        """
        # Remove potentially harmful code patterns
        sanitized_text = preprocessed_data.preprocessed_text

        # Remove any potential code injection patterns
        harmful_patterns = [
            r'\bimport\b',
            r'\bexec\b',
            r'\beval\b',
            r'\bsystem\b',
            r'\bos\.',
            r'\bsubprocess\.',
        ]

        for pattern in harmful_patterns:
            # This is a simple approach - in production, use proper input validation
            sanitized_text = re.sub(pattern, '', sanitized_text, flags=re.IGNORECASE)

        # Create new PreprocessedVoiceData with sanitized text
        sanitized_data = PreprocessedVoiceData(
            raw_audio=preprocessed_data.raw_audio,
            processed_audio=preprocessed_data.processed_audio,
            text_transcription=preprocessed_data.text_transcription,
            confidence=preprocessed_data.confidence,
            preprocessed_text=sanitized_text,
            command_structure=preprocessed_data.command_structure,
            timestamp=preprocessed_data.timestamp,
            duration=preprocessed_data.duration
        )

        return sanitized_data


def normalize_audio(audio_data: np.ndarray, target_dBFS: float = -20.0) -> np.ndarray:
    """
    Normalize audio to target loudness

    Args:
        audio_data: Audio data as numpy array
        target_dBFS: Target loudness in dB Full Scale

    Returns:
        Normalized audio data
    """
    # Calculate current loudness
    current_rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
    current_dBFS = 20 * np.log10(current_rms + 1e-9)  # Add small value to avoid log(0)

    # Calculate required gain
    gain = target_dBFS - current_dBFS
    gain_linear = 10 ** (gain / 20.0)

    # Apply gain
    normalized_audio = audio_data * gain_linear

    # Ensure values stay within bounds
    normalized_audio = np.clip(normalized_audio, -1.0, 1.0)

    return normalized_audio


def main():
    """Example usage of the voice preprocessing pipeline"""
    print("Voice Preprocessing Pipeline Example")

    # Initialize preprocessor
    preprocessor = VoicePreprocessor()
    validator = VoiceCommandValidator()

    # Example: Simulate processing of voice data
    # In a real scenario, this would come from Whisper transcription
    print("\n--- Voice Preprocessing Example ---")

    # Create some sample audio data (simulated)
    sample_rate = 16000
    duration = 2.0  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration))
    # Simulate a simple audio signal with some "speech-like" patterns
    sample_audio = (0.1 * np.sin(2 * np.pi * 440 * t) + 0.05 * np.random.randn(len(t))) * 32767
    sample_audio = sample_audio.astype(np.int16)

    # Simulated transcription
    sample_text = "Please navigate to the kitchen and find the red cup"
    sample_confidence = 0.85

    # Preprocess the voice data
    preprocessed = preprocessor.preprocess_voice_data(sample_audio, sample_text, sample_confidence)

    print(f"Original text: '{sample_text}'")
    print(f"Preprocessed text: '{preprocessed.preprocessed_text}'")
    print(f"Command structure: {preprocessed.command_structure}")
    print(f"Confidence: {preprocessed.confidence}")

    # Validate the command
    is_valid, errors = validator.validate_command(preprocessed)
    print(f"Command is valid: {is_valid}")
    if errors:
        print(f"Validation errors: {errors}")

    # Sanitize the command
    sanitized = validator.sanitize_command(preprocessed)
    print(f"Sanitized text: '{sanitized.preprocessed_text}'")

    print("\nVoice preprocessing pipeline example completed!")


if __name__ == "__main__":
    main()