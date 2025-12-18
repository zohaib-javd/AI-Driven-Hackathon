"""
Voice Command Validation and Sanitization for VLA Pipeline

This module provides validation and sanitization of voice commands
to ensure they are safe, appropriate, and properly formatted for
the Vision-Language-Action pipeline.
"""

import re
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
from urllib.parse import urlparse
import html
import json
import bleach  # For HTML sanitization

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Levels of validation to apply"""
    BASIC = "basic"
    MODERATE = "moderate"
    STRICT = "strict"
    PARANOID = "paranoid"


class ValidationStatus(Enum):
    """Status of validation result"""
    VALID = "valid"
    INVALID = "invalid"
    SUSPICIOUS = "suspicious"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Result of voice command validation"""
    is_valid: bool
    status: ValidationStatus
    sanitized_command: str
    confidence: float
    issues: List[str]
    severity: int  # 0-10 scale
    suggestions: List[str]


class VoiceCommandValidator:
    """
    Validator for voice commands with multiple levels of validation
    """

    def __init__(self, level: ValidationLevel = ValidationLevel.MODERATE):
        self.level = level
        self.max_command_length = 500  # characters
        self.min_confidence = 0.3
        self.max_execution_time = 1.0  # seconds

        # Dangerous patterns that should be blocked
        self.dangerous_patterns = [
            # Code injection patterns
            r'\bimport\b',
            r'\bexec\b',
            r'\beval\b',
            r'\bsystem\b',
            r'\bos\.',
            r'\bsubprocess\.',
            r'\b__.*__\b',  # dunder methods
            r'\bgetattr\b',
            r'\bsetattr\b',
            r'\bglobals\b',
            r'\blocals\b',
            r'\bcompile\b',
            r'\bopen\b(?!\s*\(\s*["\'][^"\']+\.\w+["\'])',  # open() without specific file

            # Shell/command patterns
            r'\bsh\b',
            r'\bbash\b',
            r'\bcmd\b',
            r'\bshell\b',
            r'\bexec\b',
            r'\brun\b(?!\s*\(\s*["\'][^"\']+\.\w+["\'])',  # run() without specific file

            # SQL injection patterns
            r'\bselect\b',
            r'\binsert\b',
            r'\bdelete\b',
            r'\bupdate\b',
            r'\bdrop\b',
            r'\bcreate\b',
            r'\balter\b',
            r'\bunion\b',
            r'\bexec\b',
            r'\b(\s|\W)or(\s|\W)',
            r'\b(\s|\W)and(\s|\W)',

            # Robot-specific dangerous commands
            r'\bshutdown\b',
            r'\breboot\b',
            r'\breset\b',
            r'\bfactory reset\b',
            r'\bformat\b',
            r'\bdelete\b',
            r'\bdestroy\b',
            r'\bkill\b',
            r'\bterminate\b',
        ]

        # Forbidden words/phrases
        self.forbidden_words = [
            'hack', 'exploit', 'vulnerability', 'security bypass',
            'admin', 'root', 'sudo', 'password', 'credential',
            'private', 'secret', 'token', 'key', 'api',
            'shutdown', 'reboot', 'reset', 'factory reset',
            'format', 'delete', 'destroy', 'kill', 'terminate'
        ]

        # Safe command patterns (for strict validation)
        self.safe_patterns = [
            r'navigate to \w+',
            r'go to \w+',
            r'move to \w+',
            r'pick up \w+',
            r'grasp \w+',
            r'place \w+',
            r'find \w+',
            r'perceive \w+',
            r'stop',
            r'pause',
            r'continue',
            r'help',
            r'status'
        ]

        # Initialize regex patterns
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for better performance"""
        self.dangerous_regexes = [re.compile(pattern, re.IGNORECASE) for pattern in self.dangerous_patterns]
        self.forbidden_regex = re.compile(r'\b(' + '|'.join(self.forbidden_words) + r')\b', re.IGNORECASE)

    def validate_command(self, command: str, confidence: float = 1.0) -> ValidationResult:
        """
        Validate a voice command with the current validation level

        Args:
            command: The voice command to validate
            confidence: Confidence score from speech recognition

        Returns:
            ValidationResult with validation details
        """
        issues = []
        suggestions = []
        severity = 0

        # Basic validation
        basic_result = self._basic_validation(command, confidence)
        if not basic_result.is_valid:
            return basic_result

        # Apply validation based on level
        if self.level in [ValidationLevel.MODERATE, ValidationLevel.STRICT, ValidationLevel.PARANOID]:
            issues, suggestions, severity = self._moderate_validation(command, issues, suggestions, severity)

        if self.level in [ValidationLevel.STRICT, ValidationLevel.PARANOID]:
            issues, suggestions, severity = self._strict_validation(command, issues, suggestions, severity)

        if self.level == ValidationLevel.PARANOID:
            issues, suggestions, severity = self._paranoid_validation(command, issues, suggestions, severity)

        # Determine final status
        status = ValidationStatus.VALID
        if severity >= 8:
            status = ValidationStatus.INVALID
        elif severity >= 5:
            status = ValidationStatus.SUSPICIOUS

        # Sanitize the command
        sanitized_command = self._sanitize_command(command)

        return ValidationResult(
            is_valid=status == ValidationStatus.VALID,
            status=status,
            sanitized_command=sanitized_command,
            confidence=confidence,
            issues=issues,
            severity=severity,
            suggestions=suggestions
        )

    def _basic_validation(self, command: str, confidence: float) -> ValidationResult:
        """Perform basic validation checks"""
        issues = []
        suggestions = []

        # Check command length
        if len(command) > self.max_command_length:
            issues.append(f"Command too long: {len(command)} chars > {self.max_command_length}")
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                sanitized_command=command[:self.max_command_length],
                confidence=confidence,
                issues=issues,
                severity=5,
                suggestions=suggestions
            )

        # Check confidence level
        if confidence < self.min_confidence:
            issues.append(f"Confidence too low: {confidence:.2f} < {self.min_confidence}")
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                sanitized_command=command,
                confidence=confidence,
                issues=issues,
                severity=3,
                suggestions=suggestions
            )

        # Check for null or empty command
        if not command or not command.strip():
            issues.append("Empty command")
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                sanitized_command=command,
                confidence=confidence,
                issues=issues,
                severity=10,
                suggestions=suggestions
            )

        return ValidationResult(
            is_valid=True,
            status=ValidationStatus.VALID,
            sanitized_command=command,
            confidence=confidence,
            issues=[],
            severity=0,
            suggestions=[]
        )

    def _moderate_validation(self, command: str, issues: List[str], suggestions: List[str], severity: int) -> Tuple[List[str], List[str], int]:
        """Perform moderate validation checks"""
        command_lower = command.lower()

        # Check for dangerous patterns
        for i, pattern in enumerate(self.dangerous_regexes):
            if pattern.search(command_lower):
                issues.append(f"Dangerous pattern detected: {self.dangerous_patterns[i]}")
                severity = max(severity, 8)

        # Check for forbidden words
        forbidden_matches = self.forbidden_regex.findall(command_lower)
        if forbidden_matches:
            issues.append(f"Forbidden words detected: {', '.join(set(forbidden_matches))}")
            severity = max(severity, 7)

        # Check for potential command injection
        injection_patterns = [
            r'[;&|]',  # Command separators
            r'\$\(',  # Command substitution
            r'`.*`',  # Backtick command substitution
            r'\$\{.*\}',  # Parameter expansion (in certain contexts)
        ]

        for pattern in injection_patterns:
            if re.search(pattern, command):
                issues.append(f"Potential command injection pattern: {pattern}")
                severity = max(severity, 8)

        return issues, suggestions, severity

    def _strict_validation(self, command: str, issues: List[str], suggestions: List[str], severity: int) -> Tuple[List[str], List[str], int]:
        """Perform strict validation checks"""
        command_lower = command.lower()

        # Only allow commands that match safe patterns
        matched_safe = any(re.match(pattern, command_lower) for pattern in self.safe_patterns)

        if not matched_safe and self.level == ValidationLevel.STRICT:
            issues.append("Command does not match any safe patterns")
            severity = max(severity, 6)
            suggestions.append("Use commands like: 'navigate to kitchen', 'pick up cup', 'find object'")

        # Additional strict checks
        # Check for URLs that might be dangerous
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, command)
        if urls:
            issues.append(f"URLs detected in command: {urls}")
            severity = max(severity, 6)

        # Check for file paths that might be dangerous
        path_patterns = [
            r'/etc/',
            r'/root/',
            r'/home/',
            r'C:\\Windows\\',
            r'C:\\Program Files',
        ]

        for pattern in path_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                issues.append(f"Potentially dangerous path pattern: {pattern}")
                severity = max(severity, 7)

        return issues, suggestions, severity

    def _paranoid_validation(self, command: str, issues: List[str], suggestions: List[str], severity: int) -> Tuple[List[str], List[str], int]:
        """Perform paranoid validation checks"""
        # In paranoid mode, only allow very simple commands
        simple_command_pattern = r'^[a-zA-Z\s]+$'  # Only letters and spaces
        if not re.match(simple_command_pattern, command.strip()):
            issues.append("Command contains non-alphabetic characters (paranoid mode)")
            severity = max(severity, 9)
            suggestions.append("Use simple alphabetic commands only")

        return issues, suggestions, severity

    def _sanitize_command(self, command: str) -> str:
        """
        Sanitize command by removing potentially harmful elements

        Args:
            command: The command to sanitize

        Returns:
            Sanitized command string
        """
        # Remove HTML tags
        sanitized = bleach.clean(command, strip=True)

        # Unescape HTML entities
        sanitized = html.unescape(sanitized)

        # Remove potentially dangerous characters/sequences
        dangerous_sequences = [
            (';', ''),  # Command separator
            ('&', ''),  # Command separator
            ('|', ''),  # Pipe operator
            ('`', ''),  # Command substitution
            ('$', ''),  # Variable expansion
            ('\\', ''),  # Escape character
        ]

        for dangerous, replacement in dangerous_sequences:
            sanitized = sanitized.replace(dangerous, replacement)

        # Remove extra whitespace
        sanitized = ' '.join(sanitized.split())

        return sanitized

    def batch_validate(self, commands: List[str], confidences: List[float]) -> List[ValidationResult]:
        """
        Validate multiple commands in batch

        Args:
            commands: List of commands to validate
            confidences: List of confidence scores

        Returns:
            List of ValidationResult objects
        """
        results = []
        for cmd, conf in zip(commands, confidences):
            result = self.validate_command(cmd, conf)
            results.append(result)
        return results

    def update_validation_level(self, new_level: ValidationLevel):
        """Update the validation level"""
        self.level = new_level
        logger.info(f"Validation level updated to: {new_level.value}")


class VoiceCommandSanitizer:
    """
    Additional sanitization utilities for voice commands
    """

    def __init__(self):
        self.sanitization_rules = [
            # Remove extra spaces
            (r'\s+', ' '),
            # Remove leading/trailing whitespace
            (r'^\s+|\s+$', ''),
            # Normalize command separators
            (r'[,\.;]+', '.'),
            # Normalize punctuation
            (r'[!?]+', '.'),
        ]

    def sanitize(self, command: str) -> str:
        """
        Apply sanitization rules to a command

        Args:
            command: Command to sanitize

        Returns:
            Sanitized command
        """
        sanitized = command

        for pattern, replacement in self.sanitization_rules:
            sanitized = re.sub(pattern, replacement, sanitized)

        return sanitized

    def normalize_command(self, command: str) -> str:
        """
        Normalize command structure

        Args:
            command: Command to normalize

        Returns:
            Normalized command
        """
        # Convert to lowercase
        normalized = command.lower()

        # Remove punctuation that might interfere with command parsing
        normalized = re.sub(r'[^\w\s]', ' ', normalized)

        # Remove extra spaces
        normalized = ' '.join(normalized.split())

        # Normalize common robot command terms
        command_mappings = {
            # Navigation
            r'\bgo to\b': 'navigate to',
            r'\bmove to\b': 'navigate to',
            r'\bwalk to\b': 'navigate to',
            r'\bgoto\b': 'navigate to',
            # Manipulation
            r'\bpick up\b': 'grasp',
            r'\bgrab\b': 'grasp',
            r'\btake\b': 'grasp',
            r'\bget\b': 'grasp',
            r'\bput down\b': 'place',
            r'\bset down\b': 'place',
            # Perception
            r'\blook at\b': 'perceive',
            r'\bsee\b': 'perceive',
            r'\bfind\b': 'perceive',
        }

        for pattern, replacement in command_mappings.items():
            normalized = re.sub(pattern, replacement, normalized)

        return normalized


class SafetyGuardrails:
    """
    Comprehensive safety guardrails for LLM-controlled robots
    """

    def __init__(self):
        self.validator = VoiceCommandValidator(level=ValidationLevel.MODERATE)
        self.sanitizer = VoiceCommandSanitizer()

    def validate_and_guard(self, command: str, confidence: float = 1.0) -> Tuple[bool, List[str], str]:
        """
        Perform comprehensive validation and safety checking

        Args:
            command: Command to validate
            confidence: Confidence score from speech recognition

        Returns:
            Tuple of (is_safe, list_of_issues, sanitized_command)
        """
        # First, validate the command
        validation_result = self.validator.validate_command(command, confidence)

        if not validation_result.is_valid:
            return False, validation_result.issues, validation_result.sanitized_command

        # Additional safety checks
        issues = validation_result.issues.copy()

        # Check for physical safety concerns
        safety_issues = self._check_physical_safety(validation_result.sanitized_command)
        issues.extend(safety_issues)

        # Check for logical safety concerns
        logical_issues = self._check_logical_safety(validation_result.sanitized_command)
        issues.extend(logical_issues)

        is_safe = len(issues) == 0 or validation_result.severity < 5

        return is_safe, issues, validation_result.sanitized_command

    def _check_physical_safety(self, command: str) -> List[str]:
        """Check for physical safety concerns in the command"""
        issues = []

        command_lower = command.lower()

        # Check for commands that might cause physical harm
        dangerous_actions = [
            r'jump',
            r'run fast',
            r'collide',
            r'crash',
            r'break',
            r'destroy',
            r'hit',
            r'attack',
            r'fight',
        ]

        for action in dangerous_actions:
            if re.search(r'\b' + action + r'\b', command_lower):
                issues.append(f"Potentially dangerous action detected: {action}")

        # Check for commands that might cause robot damage
        damaging_actions = [
            r'force',
            r'push hard',
            r'pull hard',
            r'lift heavy',
        ]

        for action in damaging_actions:
            if re.search(r'\b' + action + r'\b', command_lower):
                issues.append(f"Potentially damaging action detected: {action}")

        return issues

    def _check_logical_safety(self, command: str) -> List[str]:
        """Check for logical safety concerns in the command"""
        issues = []

        command_lower = command.lower()

        # Check for impossible or contradictory commands
        if re.search(r'stop.*while.*moving', command_lower):
            issues.append("Contradictory command: stop while moving")

        if re.search(r'go.*while.*stay', command_lower):
            issues.append("Contradictory command: go while stay")

        # Check for commands that might cause infinite loops
        if re.search(r'keep.*forever', command_lower):
            issues.append("Potentially infinite action: keep forever")

        if re.search(r'until.*never', command_lower):
            issues.append("Potentially infinite condition: until never")

        return issues


def main():
    """Example usage of the voice command validation and sanitization system"""
    print("Voice Command Validation and Sanitization Example")

    # Initialize validator
    validator = VoiceCommandValidator(level=ValidationLevel.MODERATE)
    guardrails = SafetyGuardrails()

    # Example commands to test
    test_commands = [
        "Please navigate to the kitchen and find the red cup",
        "Go to the living room and pick up the book",
        "Move to the table and place the object",
        "Stop the robot immediately",  # Potentially dangerous
        "import os; os.system('rm -rf /')",  # Code injection attempt
        "Go to the kitchen and pick up the cup with the red color",  # Safe command
        "shutdown the system",  # Potentially dangerous
    ]

    print("\n--- Validation Examples ---")
    for i, cmd in enumerate(test_commands):
        print(f"\nCommand {i+1}: '{cmd}'")

        # Validate the command
        result = validator.validate_command(cmd, confidence=0.85)
        print(f"  Valid: {result.is_valid}")
        print(f"  Status: {result.status.value}")
        print(f"  Severity: {result.severity}")
        print(f"  Sanitized: '{result.sanitized_command}'")

        if result.issues:
            print(f"  Issues: {result.issues}")

        if result.suggestions:
            print(f"  Suggestions: {result.suggestions}")

        # Test safety guardrails
        is_safe, safety_issues, safe_command = guardrails.validate_and_guard(cmd, 0.85)
        print(f"  Safe: {is_safe}")
        if safety_issues:
            print(f"  Safety Issues: {safety_issues}")

    print("\n--- Validation Level Examples ---")
    for level in [ValidationLevel.BASIC, ValidationLevel.MODERATE, ValidationLevel.STRICT]:
        print(f"\nTesting with {level.value} validation level:")
        validator.update_validation_level(level)

        test_cmd = "Go to the kitchen and pick up the cup"
        result = validator.validate_command(test_cmd, confidence=0.9)
        print(f"  Command: '{test_cmd}' -> Valid: {result.is_valid}, Issues: {len(result.issues)}")

    print("\nVoice command validation and sanitization example completed!")


if __name__ == "__main__":
    main()