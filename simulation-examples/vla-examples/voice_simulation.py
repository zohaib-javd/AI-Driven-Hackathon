"""
Voice Command Simulation Environment for VLA Pipeline

This module provides a simulation environment for voice commands in the
Vision-Language-Action pipeline, including mock Whisper responses,
command simulation, and testing utilities.
"""

import asyncio
import random
import time
import json
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
import threading
import queue
import tempfile
import os
from pathlib import Path

from whisper_api import WhisperResponse, WhisperErrorType
from voice_validation import VoiceCommandValidator, ValidationLevel, ValidationResult


class VoiceSimulationMode(Enum):
    """Different modes for voice command simulation"""
    MOCK = "mock"
    SYNTHETIC = "synthetic"
    RECORDED = "recorded"
    MIXED = "mixed"


@dataclass
class SimulatedVoiceCommand:
    """Represents a simulated voice command with metadata"""
    original_text: str
    simulated_audio: Optional[np.ndarray] = None
    transcription: str = ""
    confidence: float = 0.0
    timestamp: float = 0.0
    noise_level: float = 0.0
    accent: str = "neutral"
    speaker_id: str = "default"
    processing_time: float = 0.0
    validation_result: Optional[ValidationResult] = None


class VoiceCommandSimulator:
    """
    Simulator for voice commands in VLA pipeline
    Generates realistic voice commands with various characteristics
    """

    def __init__(self, mode: VoiceSimulationMode = VoiceSimulationMode.MOCK):
        self.mode = mode
        self.validator = VoiceCommandValidator(level=ValidationLevel.MODERATE)

        # Common voice commands for robotics
        self.command_templates = [
            "navigate to the {location}",
            "go to the {location}",
            "move to the {location}",
            "go to the {location} and {action} the {object}",
            "find the {object} in the {location}",
            "pick up the {color} {object}",
            "grasp the {object}",
            "place the {object} on the {surface}",
            "perceive the {object}",
            "detect the {object}",
            "stop the robot",
            "pause execution",
            "continue",
            "help",
            "status",
            "reset system"
        ]

        # Common locations
        self.locations = [
            "kitchen", "living room", "bedroom", "office", "garage",
            "hallway", "bathroom", "dining room", "study", "workshop"
        ]

        # Common objects
        self.objects = [
            "cup", "bottle", "book", "phone", "keys", "pen", "paper",
            "plate", "fork", "knife", "spoon", "napkin", "glass", "box",
            "ball", "toy", "remote", "laptop", "tablet", "wallet"
        ]

        # Common colors
        self.colors = [
            "red", "blue", "green", "yellow", "black", "white",
            "orange", "purple", "pink", "brown", "gray", "silver"
        ]

        # Common actions
        self.actions = [
            "pick up", "grasp", "take", "lift", "hold", "carry",
            "move", "transport", "bring", "fetch", "get"
        ]

        # Common surfaces
        self.surfaces = [
            "table", "counter", "desk", "shelf", "cabinet",
            "floor", "chair", "sofa", "bed", "drawer"
        ]

        # Accents and variations
        self.accent_variations = {
            "neutral": 0.1,
            "slight_stutter": 0.05,
            "background_noise": 0.15,
            "accent_variation": 0.1,
            "speaking_speed": 0.1
        }

        print(f"Voice Command Simulator initialized in {mode.value} mode")

    def generate_command(self) -> str:
        """Generate a realistic voice command"""
        template = random.choice(self.command_templates)

        # Fill in template with random values
        command = template.format(
            location=random.choice(self.locations),
            object=random.choice(self.objects),
            color=random.choice(self.colors),
            action=random.choice(self.actions),
            surface=random.choice(self.surfaces)
        )

        # Apply accent variations
        command = self._apply_accent_variation(command)

        return command

    def _apply_accent_variation(self, command: str) -> str:
        """Apply realistic accent variations to the command"""
        variation = random.choices(
            list(self.accent_variations.keys()),
            weights=list(self.accent_variations.values())
        )[0]

        if variation == "slight_stutter":
            # Add slight stuttering
            words = command.split()
            for i in range(min(2, len(words))):
                idx = random.randint(0, len(words)-1)
                words[idx] = f"{words[idx][:2]}-{words[idx]}"
            command = " ".join(words)

        elif variation == "accent_variation":
            # Apply common pronunciation variations
            replacements = {
                "navigate": "nav-i-gate",
                "kitchen": "kitch-en",
                "computer": "comp-you-ter",
                "robot": "ro-bought"
            }

            for original, replacement in replacements.items():
                if original in command:
                    if random.random() < 0.3:  # 30% chance to apply variation
                        command = command.replace(original, replacement)

        return command

    def simulate_whisper_response(self, command: str, noise_level: float = 0.0) -> WhisperResponse:
        """Simulate Whisper API response with configurable noise and imperfections"""
        start_time = time.time()

        # Add some randomness to simulate real transcription errors
        transcription = command.lower()

        # Simulate transcription errors based on noise level
        if noise_level > 0.0:
            transcription = self._simulate_transcription_errors(transcription, noise_level)

        # Calculate simulated confidence (lower for more errors)
        error_count = sum(c1 != c2 for c1, c2 in zip(command.lower(), transcription))
        base_confidence = 0.95
        confidence_reduction = min(0.5, error_count * 0.02)
        confidence = max(0.3, base_confidence - confidence_reduction)

        processing_time = time.time() - start_time

        return WhisperResponse(
            text=transcription,
            language="en",
            duration=len(transcription) / 100.0,  # Simulated duration
            segments=[],
            confidence=confidence,
            processing_time=processing_time
        )

    def _simulate_transcription_errors(self, text: str, noise_level: float) -> str:
        """Simulate transcription errors based on noise level"""
        # Possible error types and their probabilities based on noise level
        errors = []

        # Character substitution (similar sounding words)
        substitutions = {
            'kitchen': 'chicken', 'navigate': 'navigate', 'robot': 'lobot',
            'find': 'fine', 'the': 'de', 'and': 'end', 'to': 'too'
        }

        words = text.split()
        for i, word in enumerate(words):
            if random.random() < noise_level * 0.3:  # 30% chance per word at max noise
                # Try to substitute with similar word
                for orig, subst in substitutions.items():
                    if word.startswith(orig[:2]):  # Match first 2 characters
                        words[i] = subst
                        break

        # Add random insertions/deletions
        if random.random() < noise_level * 0.2:
            # Insert extra word occasionally
            idx = random.randint(0, len(words))
            words.insert(idx, random.choice(['um', 'uh', 'ah']))

        if random.random() < noise_level * 0.15 and len(words) > 1:
            # Remove word occasionally
            idx = random.randint(0, len(words) - 1)
            words.pop(idx)

        return " ".join(words)

    def simulate_audio_generation(self, text: str, duration: float = 2.0) -> np.ndarray:
        """Simulate audio generation for the text (mock implementation)"""
        sample_rate = 16000  # Standard for Whisper
        num_samples = int(sample_rate * duration)

        # Generate simple mock audio - a combination of different frequencies
        # representing speech patterns
        t = np.linspace(0, duration, num_samples)

        # Base frequency for speech (average human voice ~200Hz)
        base_freq = 200 + random.uniform(-50, 50)

        # Generate a complex waveform representing speech
        audio_signal = np.zeros(num_samples)

        # Add multiple harmonics to simulate speech
        for harmonic in range(1, 6):
            freq = base_freq * harmonic
            # Add some randomness to frequencies
            freq += random.uniform(-20, 20)

            # Create a segment with varying amplitude
            segment_duration = duration / len(text.split())
            for i, word in enumerate(text.split()):
                start_idx = int(i * segment_duration * sample_rate)
                end_idx = min(int((i + 1) * segment_duration * sample_rate), num_samples)

                if start_idx < num_samples:
                    t_segment = t[start_idx:end_idx]
                    amplitude = 0.3 + random.uniform(0.1, 0.2)

                    # Add some modulation to simulate speech patterns
                    mod_freq = 5 + len(word) * 2  # Modulate based on word length
                    modulation = 1 + 0.3 * np.sin(2 * np.pi * mod_freq * t_segment)

                    wave = amplitude * modulation * np.sin(2 * np.pi * freq * t_segment)
                    audio_signal[start_idx:end_idx] += wave * 0.3

        # Add some background noise
        noise = np.random.normal(0, 0.05, num_samples)
        audio_signal += noise

        # Normalize to prevent clipping
        audio_signal = audio_signal / np.max(np.abs(audio_signal)) * 0.8

        return audio_signal.astype(np.float32)

    def simulate_voice_command(self, command: Optional[str] = None,
                             noise_level: float = 0.0) -> SimulatedVoiceCommand:
        """Simulate a complete voice command with audio and transcription"""
        if command is None:
            command = self.generate_command()

        start_time = time.time()

        # Generate mock audio
        audio = self.simulate_audio_generation(command)

        # Simulate Whisper transcription
        whisper_response = self.simulate_whisper_response(command, noise_level)

        # Validate the command
        validation_result = self.validator.validate_command(whisper_response.text, whisper_response.confidence)

        processing_time = time.time() - start_time

        return SimulatedVoiceCommand(
            original_text=command,
            simulated_audio=audio,
            transcription=whisper_response.text,
            confidence=whisper_response.confidence,
            timestamp=time.time(),
            noise_level=noise_level,
            accent="neutral",  # Could be randomized
            speaker_id=f"speaker_{random.randint(1000, 9999)}",
            processing_time=processing_time,
            validation_result=validation_result
        )

    def batch_simulate(self, count: int, noise_levels: Optional[List[float]] = None) -> List[SimulatedVoiceCommand]:
        """Simulate multiple voice commands"""
        if noise_levels is None:
            noise_levels = [random.uniform(0.0, 0.3) for _ in range(count)]

        commands = []
        for i in range(count):
            noise = noise_levels[i] if i < len(noise_levels) else random.uniform(0.0, 0.3)
            cmd = self.simulate_voice_command(noise_level=noise)
            commands.append(cmd)

        return commands


class VoiceSimulationEnvironment:
    """
    Full simulation environment for testing voice command systems
    """

    def __init__(self, simulator: VoiceCommandSimulator):
        self.simulator = simulator
        self.active_listening = False
        self.command_queue = queue.Queue()
        self.results_log = []
        self.stats = {
            "total_commands": 0,
            "successful_transcriptions": 0,
            "validation_passes": 0,
            "avg_confidence": 0.0,
            "avg_processing_time": 0.0
        }

    def start_continuous_simulation(self, callback: Callable[[SimulatedVoiceCommand], None]):
        """Start continuous voice command simulation"""
        self.active_listening = True

        def simulation_loop():
            while self.active_listening:
                try:
                    # Simulate a new command
                    cmd = self.simulate_single_command()

                    # Add to results log
                    self.results_log.append(cmd)

                    # Update statistics
                    self._update_statistics(cmd)

                    # Call the callback with the simulated command
                    callback(cmd)

                    # Wait a bit before next command (simulate natural speaking pace)
                    time.sleep(random.uniform(2.0, 5.0))

                except Exception as e:
                    print(f"Error in simulation loop: {e}")
                    time.sleep(1.0)  # Wait before retrying

        # Start the simulation loop in a separate thread
        simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
        simulation_thread.start()

        return simulation_thread

    def simulate_single_command(self, command: Optional[str] = None,
                              noise_level: float = 0.0) -> SimulatedVoiceCommand:
        """Simulate a single command"""
        return self.simulator.simulate_voice_command(command, noise_level)

    def _update_statistics(self, cmd: SimulatedVoiceCommand):
        """Update simulation statistics"""
        self.stats["total_commands"] += 1

        if cmd.confidence > 0.5:
            self.stats["successful_transcriptions"] += 1

        if cmd.validation_result and cmd.validation_result.is_valid:
            self.stats["validation_passes"] += 1

        # Update averages
        total = self.stats["total_commands"]
        self.stats["avg_confidence"] = ((self.stats["avg_confidence"] * (total - 1) + cmd.confidence) / total)
        self.stats["avg_processing_time"] = ((self.stats["avg_processing_time"] * (total - 1) + cmd.processing_time) / total)

    def get_statistics(self) -> Dict[str, Any]:
        """Get current simulation statistics"""
        return self.stats.copy()

    def stop_simulation(self):
        """Stop the continuous simulation"""
        self.active_listening = False

    def export_results(self, filepath: str):
        """Export simulation results to JSON file"""
        results_data = []
        for cmd in self.results_log:
            cmd_dict = {
                "original_text": cmd.original_text,
                "transcription": cmd.transcription,
                "confidence": cmd.confidence,
                "timestamp": cmd.timestamp,
                "noise_level": cmd.noise_level,
                "processing_time": cmd.processing_time,
                "validation_result": {
                    "is_valid": cmd.validation_result.is_valid if cmd.validation_result else None,
                    "status": cmd.validation_result.status.value if cmd.validation_result else None,
                    "issues": cmd.validation_result.issues if cmd.validation_result else [],
                    "severity": cmd.validation_result.severity if cmd.validation_result else 0
                } if cmd.validation_result else None
            }
            results_data.append(cmd_dict)

        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"Results exported to {filepath}")


class VoiceCommandTestSuite:
    """
    Comprehensive test suite for voice command validation and processing
    """

    def __init__(self, simulator: VoiceCommandSimulator):
        self.simulator = simulator
        self.tests_passed = 0
        self.tests_total = 0

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests in the suite"""
        print("Running Voice Command Test Suite...")

        results = {
            "basic_functionality": self.test_basic_functionality(),
            "validation_tests": self.test_validation_scenarios(),
            "edge_cases": self.test_edge_cases(),
            "performance": self.test_performance(),
            "accuracy": self.test_accuracy()
        }

        summary = {
            "passed": self.tests_passed,
            "total": self.tests_total,
            "success_rate": self.tests_passed / self.tests_total if self.tests_total > 0 else 0
        }

        results["summary"] = summary
        print(f"Test Suite Complete: {self.tests_passed}/{self.tests_total} tests passed")

        return results

    def test_basic_functionality(self) -> Dict[str, Any]:
        """Test basic voice command functionality"""
        print("  Testing basic functionality...")

        try:
            # Test command generation
            cmd = self.simulator.generate_command()
            assert isinstance(cmd, str) and len(cmd) > 0

            # Test transcription simulation
            response = self.simulator.simulate_whisper_response(cmd)
            assert isinstance(response.text, str)
            assert 0.0 <= response.confidence <= 1.0

            # Test audio generation
            audio = self.simulator.simulate_audio_generation(cmd)
            assert isinstance(audio, np.ndarray)
            assert len(audio) > 0

            # Test validation
            validation = self.simulator.validator.validate_command(response.text, response.confidence)
            assert isinstance(validation, ValidationResult)

            self.tests_passed += 1
            return {"status": "pass", "message": "Basic functionality works"}

        except Exception as e:
            self.tests_total += 1
            return {"status": "fail", "message": f"Basic functionality failed: {e}"}

    def test_validation_scenarios(self) -> Dict[str, Any]:
        """Test various validation scenarios"""
        print("  Testing validation scenarios...")

        scenarios = [
            ("Valid command", "navigate to kitchen", True),
            ("Empty command", "", False),
            ("Dangerous command", "import os; os.system('rm -rf /')", False),
            ("Long command", " ".join(["word"] * 600), False),  # Too long
        ]

        passed = 0
        for desc, cmd, should_be_valid in scenarios:
            try:
                result = self.simulator.validator.validate_command(cmd, 0.9)
                if result.is_valid == should_be_valid:
                    passed += 1
                else:
                    print(f"    Validation mismatch for '{desc}': expected {should_be_valid}, got {result.is_valid}")
            except Exception as e:
                print(f"    Error testing '{desc}': {e}")

        self.tests_total += len(scenarios)
        self.tests_passed += passed

        return {
            "status": "pass" if passed == len(scenarios) else "partial",
            "message": f"Validation: {passed}/{len(scenarios)} scenarios passed"
        }

    def test_edge_cases(self) -> Dict[str, Any]:
        """Test edge cases and error conditions"""
        print("  Testing edge cases...")

        edge_cases = [
            ("High noise", lambda: self.simulator.simulate_whisper_response("hello", noise_level=0.9)),
            ("Low confidence", lambda: self.simulator.simulate_whisper_response("test command", noise_level=0.8)),
            ("Special characters", lambda: self.simulator.simulate_whisper_response("test @#$% command")),
            ("Numbers and symbols", lambda: self.simulator.simulate_whisper_response("go to room 3a")),
        ]

        passed = 0
        for desc, test_func in edge_cases:
            try:
                result = test_func()
                assert result is not None
                passed += 1
            except Exception as e:
                print(f"    Edge case '{desc}' failed: {e}")

        self.tests_total += len(edge_cases)
        self.tests_passed += passed

        return {
            "status": "pass" if passed == len(edge_cases) else "partial",
            "message": f"Edge cases: {passed}/{len(edge_cases)} passed"
        }

    def test_performance(self) -> Dict[str, Any]:
        """Test performance under load"""
        print("  Testing performance...")

        try:
            start_time = time.time()

            # Generate and process many commands
            commands = self.simulator.batch_simulate(50)

            elapsed = time.time() - start_time
            avg_time = elapsed / len(commands) if commands else 0

            # Check if performance is acceptable (arbitrary threshold)
            if avg_time < 0.5:  # Less than 0.5 seconds per command
                self.tests_passed += 1
                return {
                    "status": "pass",
                    "message": f"Performance: {avg_time:.3f}s per command, {elapsed:.2f}s total"
                }
            else:
                return {
                    "status": "fail",
                    "message": f"Performance too slow: {avg_time:.3f}s per command"
                }

        except Exception as e:
            return {"status": "fail", "message": f"Performance test failed: {e}"}

    def test_accuracy(self) -> Dict[str, Any]:
        """Test transcription accuracy"""
        print("  Testing accuracy...")

        try:
            # Test with low noise - should have high accuracy
            original = "navigate to the kitchen"
            response_low_noise = self.simulator.simulate_whisper_response(original, noise_level=0.1)

            # Test with high noise - accuracy may suffer
            response_high_noise = self.simulator.simulate_whisper_response(original, noise_level=0.7)

            # Basic check: low noise should have higher confidence than high noise
            if response_low_noise.confidence >= response_high_noise.confidence:
                self.tests_passed += 1
                return {
                    "status": "pass",
                    "message": f"Accuracy: low noise ({response_low_noise.confidence:.2f}) >= high noise ({response_high_noise.confidence:.2f})"
                }
            else:
                return {
                    "status": "fail",
                    "message": "Accuracy test failed: high noise had higher confidence than low noise"
                }

        except Exception as e:
            return {"status": "fail", "message": f"Accuracy test failed: {e}"}


def main():
    """Example usage of the voice simulation environment"""
    print("Voice Command Simulation Environment Example")

    # Initialize simulator
    simulator = VoiceCommandSimulator(mode=VoiceSimulationMode.MOCK)

    # Example 1: Generate and simulate a single command
    print("\n--- Single Command Simulation ---")
    sim_cmd = simulator.simulate_voice_command("Navigate to the kitchen and find the red cup")
    print(f"Original: '{sim_cmd.original_text}'")
    print(f"Transcription: '{sim_cmd.transcription}'")
    print(f"Confidence: {sim_cmd.confidence:.3f}")
    print(f"Valid: {sim_cmd.validation_result.is_valid if sim_cmd.validation_result else 'N/A'}")

    # Example 2: Batch simulation
    print("\n--- Batch Simulation ---")
    batch_commands = simulator.batch_simulate(5)
    for i, cmd in enumerate(batch_commands):
        print(f"  Cmd {i+1}: '{cmd.original_text}' -> '{cmd.transcription}' (conf: {cmd.confidence:.3f})")

    # Example 3: Validation testing
    print("\n--- Validation Testing ---")
    test_suite = VoiceCommandTestSuite(simulator)
    results = test_suite.run_all_tests()

    print(f"\nTest Results Summary:")
    for category, result in results.items():
        if category != "summary":
            print(f"  {category}: {result['message']}")

    print(f"  Overall: {results['summary']['passed']}/{results['summary']['total']} tests passed "
          f"({results['summary']['success_rate']*100:.1f}%)")

    # Example 4: Simulation environment
    print("\n--- Simulation Environment ---")
    env = VoiceSimulationEnvironment(simulator)

    # Simple callback to handle simulated commands
    def handle_command(cmd: SimulatedVoiceCommand):
        print(f"  Received: '{cmd.transcription}' (conf: {cmd.confidence:.3f}, valid: {cmd.validation_result.is_valid if cmd.validation_result else 'N/A'})")

    # Just demonstrate the concept without actually running continuously
    print("  Simulation environment ready (not running continuously for this demo)")
    print(f"  Current stats: {env.get_statistics()}")

    print("\nVoice simulation environment example completed!")


if __name__ == "__main__":
    main()