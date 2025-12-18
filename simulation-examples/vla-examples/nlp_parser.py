"""
Natural Language Parser for Robot Commands in VLA Pipeline

This module provides comprehensive parsing of natural language commands
into structured robot actions for the Vision-Language-Action pipeline.
"""

import re
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
import openai
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RobotActionType(Enum):
    """Types of robot actions"""
    NAVIGATE = "navigate"
    GRASP = "grasp"
    PLACE = "place"
    FIND = "find"
    DETECT = "detect"
    INSPECT = "inspect"
    MOVE = "move"
    ALIGN = "align"
    TRANSPORT = "transport"
    STOP = "stop"
    PAUSE = "pause"
    CONTINUE = "continue"
    UNKNOWN = "unknown"


class CommandParsingStatus(Enum):
    """Status of command parsing"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    AMBIGUOUS = "ambiguous"


@dataclass
class ParsedCommand:
    """Represents a parsed robot command"""
    action: RobotActionType
    target: str
    parameters: Dict[str, Any]
    confidence: float
    original_text: str
    entities: Dict[str, List[str]]
    dependencies: List[str]
    status: CommandParsingStatus
    reasoning: str


@dataclass
class ParseResult:
    """Result of command parsing"""
    success: bool
    commands: List[ParsedCommand]
    confidence: float
    errors: List[str]
    warnings: List[str]


class IntentClassifier:
    """
    Classifier for identifying the intent of robot commands
    """

    def __init__(self):
        # Predefined intent patterns
        self.intent_patterns = {
            RobotActionType.NAVIGATE: [
                r'\bgo to\b',
                r'\bmove to\b',
                r'\bnavigate to\b',
                r'\bwalk to\b',
                r'\btravel to\b',
                r'\bhead to\b',
                r'\bmove toward\b',
                r'\bproceed to\b',
            ],
            RobotActionType.GRASP: [
                r'\bpick up\b',
                r'\bgrasp\b',
                r'\btake\b',
                r'\bgrab\b',
                r'\blift\b',
                r'\bget\b',
                r'\bretrieve\b',
                r'\bcapture\b',
            ],
            RobotActionType.PLACE: [
                r'\bplace\b',
                r'\bput\b',
                r'\bset down\b',
                r'\bdeposit\b',
                r'\bposition\b',
                r'\blocate\b',
                r'\bdrop\b',
            ],
            RobotActionType.FIND: [
                r'\bfind\b',
                r'\blocate\b',
                r'\bsearch for\b',
                r'\blook for\b',
                r'\bdetect\b',
                r'\bidentify\b',
                r'\bspot\b',
                r'\bseek\b',
            ],
            RobotActionType.STOP: [
                r'\bstop\b',
                r'\bhalt\b',
                r'\bpause\b',
                r'\bfreeze\b',
                r'\bcease\b',
                r'\bend\b',
            ],
            RobotActionType.CONTINUE: [
                r'\bcontinue\b',
                r'\bresume\b',
                r'\bproceed\b',
                r'\brestart\b',
                r'\bcarry on\b',
            ]
        }

        # Compile regex patterns for better performance
        self.compiled_patterns = {}
        for action_type, patterns in self.intent_patterns.items():
            compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
            self.compiled_patterns[action_type] = compiled_patterns

    def classify_intent(self, command: str) -> Tuple[RobotActionType, float]:
        """
        Classify the intent of a command

        Args:
            command: The command to classify

        Returns:
            Tuple of (intent, confidence)
        """
        best_match = RobotActionType.UNKNOWN
        best_confidence = 0.0

        command_lower = command.lower()

        for action_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(command_lower):
                    # Calculate confidence based on match quality
                    match = pattern.search(command_lower)
                    if match:
                        # More specific matches get higher confidence
                        confidence = min(1.0, 0.5 + len(match.group()) / len(command_lower))
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = action_type

        return best_match, best_confidence


class EntityExtractor:
    """
    Extractor for identifying entities in robot commands
    """

    def __init__(self):
        # Common entity patterns
        self.object_patterns = [
            r'\b(red|blue|green|yellow|black|white|orange|purple|pink|brown)\s+(\w+)\b',
            r'\b(small|large|big|tiny|medium)\s+(\w+)\b',
            r'\b(\w+)\s+(cup|bottle|book|phone|keys|pen|glass|plate|box|ball|toy|object)\b',
            r'\b(a|an)\s+(\w+)\b',
        ]

        self.location_patterns = [
            r'\b(kitchen|living room|bedroom|office|garage|hallway|bathroom|dining room|study|workshop)\b',
            r'\b(table|counter|desk|shelf|cabinet|floor|chair|sofa|bed|drawer)\b',
        ]

        self.quantity_patterns = [
            r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\b',
            r'\b(\d+)\b',
        ]

        self.spatial_patterns = [
            r'\b(left|right|front|behind|near|far|above|below|beside|between|next to|across from)\b',
        ]

        # Compile patterns
        self.compiled_object_patterns = [re.compile(p, re.IGNORECASE) for p in self.object_patterns]
        self.compiled_location_patterns = [re.compile(p, re.IGNORECASE) for p in self.location_patterns]
        self.compiled_quantity_patterns = [re.compile(p, re.IGNORECASE) for p in self.quantity_patterns]
        self.compiled_spacial_patterns = [re.compile(p, re.IGNORECASE) for p in self.spatial_patterns]

    def extract_entities(self, command: str) -> Dict[str, List[str]]:
        """
        Extract entities from a command

        Args:
            command: The command to extract entities from

        Returns:
            Dictionary of entity types and their values
        """
        entities = {
            'objects': [],
            'locations': [],
            'quantities': [],
            'spatial_relations': [],
            'colors': [],
            'sizes': []
        }

        command_lower = command.lower()

        # Extract objects
        for pattern in self.compiled_object_patterns:
            matches = pattern.findall(command_lower)
            for match in matches:
                if isinstance(match, tuple):
                    if len(match) == 2:
                        if match[0].lower() in ['red', 'blue', 'green', 'yellow', 'black', 'white', 'orange', 'purple', 'pink', 'brown']:
                            entities['colors'].append(match[0])
                        elif match[0].lower() in ['small', 'large', 'big', 'tiny', 'medium']:
                            entities['sizes'].append(match[0])
                        entities['objects'].append(match[1])
                    elif len(match) == 1:
                        entities['objects'].append(match[0])

        # Extract locations
        for pattern in self.compiled_location_patterns:
            matches = pattern.findall(command_lower)
            entities['locations'].extend([match if isinstance(match, str) else match[0] for match in matches])

        # Extract quantities
        for pattern in self.compiled_quantity_patterns:
            matches = pattern.findall(command_lower)
            entities['quantities'].extend([match if isinstance(match, str) else match[0] for match in matches])

        # Extract spatial relations
        for pattern in self.compiled_spacial_patterns:
            matches = pattern.findall(command_lower)
            entities['spatial_relations'].extend([match if isinstance(match, str) else match[0] for match in matches])

        # Remove duplicates
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities


class SemanticAnalyzer:
    """
    Analyzer for understanding the semantic meaning of commands
    """

    def __init__(self):
        # Initialize sentence transformer model for semantic similarity
        try:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        except:
            logger.warning("Sentence transformer model not available, using basic similarity")
            self.sentence_model = None

        # Define command templates with expected semantic structures
        self.command_templates = {
            "navigate_to_location": {
                "patterns": ["go to", "move to", "navigate to", "walk to"],
                "required_entities": ["location"],
                "optional_entities": ["object"]
            },
            "grasp_object": {
                "patterns": ["pick up", "grasp", "take", "grab"],
                "required_entities": ["object"],
                "optional_entities": ["location", "color", "size"]
            },
            "place_object": {
                "patterns": ["place", "put", "set down", "deposit"],
                "required_entities": ["object", "location"],
                "optional_entities": ["color", "size"]
            },
            "find_object": {
                "patterns": ["find", "locate", "search for", "look for"],
                "required_entities": ["object"],
                "optional_entities": ["location", "color", "size"]
            }
        }

    def analyze_semantics(self, command: str, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Analyze the semantic structure of a command

        Args:
            command: The command to analyze
            entities: Extracted entities

        Returns:
            Semantic analysis results
        """
        analysis = {
            "template_match": None,
            "confidence": 0.0,
            "missing_entities": [],
            "semantic_similarity": 0.0
        }

        command_lower = command.lower()

        # Find best template match
        best_template = None
        best_confidence = 0.0

        for template_name, template_def in self.command_templates.items():
            for pattern in template_def["patterns"]:
                if pattern in command_lower:
                    confidence = len(pattern) / len(command_lower)  # Simple confidence measure
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_template = template_name
                        break

        if best_template:
            analysis["template_match"] = best_template
            analysis["confidence"] = best_confidence

            # Check for required entities
            required = self.command_templates[best_template]["required_entities"]
            missing = []
            for req in required:
                if not entities.get(req):
                    missing.append(req)
            analysis["missing_entities"] = missing

            # Calculate semantic similarity if model available
            if self.sentence_model:
                try:
                    embeddings = self.sentence_model.encode([command])
                    # In a real implementation, we'd compare to known good examples
                    analysis["semantic_similarity"] = 0.8  # Placeholder
                except:
                    analysis["semantic_similarity"] = 0.5

        return analysis


class NLPRobotParser:
    """
    Main natural language parser for robot commands
    """

    def __init__(self, use_llm_enhancement: bool = True):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        self.semantic_analyzer = SemanticAnalyzer()
        self.use_llm_enhancement = use_llm_enhancement

        # LLM enhancement parameters
        self.llm_model = "gpt-4" if use_llm_enhancement else None

        logger.info("NLP Robot Parser initialized")

    def parse_command(self, command: str) -> ParseResult:
        """
        Parse a natural language command into structured robot actions

        Args:
            command: Natural language command to parse

        Returns:
            ParseResult with parsed commands and metadata
        """
        errors = []
        warnings = []

        # Validate input
        if not command or not command.strip():
            errors.append("Empty command provided")
            return ParseResult(success=False, commands=[], confidence=0.0, errors=errors, warnings=warnings)

        original_command = command.strip()

        try:
            # Step 1: Classify intent
            intent, intent_confidence = self.intent_classifier.classify_intent(original_command)

            # Step 2: Extract entities
            entities = self.entity_extractor.extract_entities(original_command)

            # Step 3: Semantic analysis
            semantics = self.semantic_analyzer.analyze_semantics(original_command, entities)

            # Step 4: Create parameters dictionary
            parameters = self._create_parameters(entities, semantics)

            # Step 5: Generate reasoning
            reasoning = self._generate_reasoning(original_command, intent, entities, semantics)

            # Step 6: Determine status
            status = self._determine_status(semantics, intent_confidence)

            # Step 7: Create parsed command
            parsed_command = ParsedCommand(
                action=intent,
                target=self._extract_target(entities),
                parameters=parameters,
                confidence=intent_confidence,
                original_text=original_command,
                entities=entities,
                dependencies=self._extract_dependencies(entities),
                status=status,
                reasoning=reasoning
            )

            # Apply LLM enhancement if enabled
            if self.use_llm_enhancement and self.llm_model:
                try:
                    enhanced_command = self._enhance_with_llm(parsed_command)
                    parsed_command = enhanced_command
                except Exception as e:
                    logger.warning(f"LLM enhancement failed: {e}")
                    warnings.append(f"LLM enhancement failed: {e}")

            # Validate the parsed command
            validation_result = self._validate_parsed_command(parsed_command)
            if not validation_result['is_valid']:
                status = CommandParsingStatus.AMBIGUOUS
                parsed_command.status = status
                warnings.extend(validation_result['issues'])

            return ParseResult(
                success=True,
                commands=[parsed_command],
                confidence=parsed_command.confidence,
                errors=errors,
                warnings=warnings
            )

        except Exception as e:
            errors.append(f"Parsing error: {str(e)}")
            logger.error(f"Error parsing command '{original_command}': {e}")
            return ParseResult(
                success=False,
                commands=[],
                confidence=0.0,
                errors=errors,
                warnings=warnings
            )

    def _create_parameters(self, entities: Dict[str, List[str]], semantics: Dict[str, Any]) -> Dict[str, Any]:
        """Create parameters dictionary from extracted entities"""
        parameters = {}

        # Add object properties
        if entities.get('colors'):
            parameters['color'] = entities['colors'][0]  # Take first color
        if entities.get('sizes'):
            parameters['size'] = entities['sizes'][0]  # Take first size

        # Add location if present
        if entities.get('locations'):
            parameters['location'] = entities['locations'][0]

        # Add quantities
        if entities.get('quantities'):
            try:
                parameters['quantity'] = int(entities['quantities'][0])
            except ValueError:
                parameters['quantity'] = entities['quantities'][0]

        # Add spatial relations
        if entities.get('spatial_relations'):
            parameters['spatial_relation'] = entities['spatial_relations'][0]

        # Add semantic info
        if semantics.get('template_match'):
            parameters['template'] = semantics['template_match']

        return parameters

    def _extract_target(self, entities: Dict[str, List[str]]) -> str:
        """Extract target from entities"""
        if entities.get('objects'):
            return entities['objects'][0]
        elif entities.get('locations'):
            return entities['locations'][0]
        elif entities.get('spatial_relations'):
            return entities['spatial_relations'][0]
        return "unknown"

    def _extract_dependencies(self, entities: Dict[str, List[str]]) -> List[str]:
        """Extract dependencies from entities"""
        dependencies = []

        # If we have both object and location, there might be a dependency
        if entities.get('objects') and entities.get('locations'):
            dependencies.append(f"navigate_to_{entities['locations'][0]}")

        return dependencies

    def _generate_reasoning(self, command: str, intent: RobotActionType, entities: Dict[str, List[str]], semantics: Dict[str, Any]) -> str:
        """Generate reasoning for the parsed command"""
        reasoning_parts = []

        # Add intent reasoning
        if intent != RobotActionType.UNKNOWN:
            reasoning_parts.append(f"Identified intent as {intent.value} based on command pattern matching.")

        # Add entity reasoning
        if entities.get('objects'):
            reasoning_parts.append(f"Detected objects: {', '.join(entities['objects'])}")
        if entities.get('locations'):
            reasoning_parts.append(f"Detected locations: {', '.join(entities['locations'])}")

        # Add semantic reasoning
        if semantics.get('template_match'):
            reasoning_parts.append(f"Matches template '{semantics['template_match']}' with confidence {semantics.get('confidence', 0):.2f}")

        return " ".join(reasoning_parts) if reasoning_parts else "Command parsed using pattern matching."

    def _determine_status(self, semantics: Dict[str, Any], confidence: float) -> CommandParsingStatus:
        """Determine parsing status based on semantics and confidence"""
        if confidence < 0.3:
            return CommandParsingStatus.FAILURE
        elif semantics.get('missing_entities') and semantics['missing_entities']:
            return CommandParsingStatus.AMBIGUOUS
        elif confidence < 0.7:
            return CommandParsingStatus.PARTIAL_SUCCESS
        else:
            return CommandParsingStatus.SUCCESS

    def _validate_parsed_command(self, command: ParsedCommand) -> Dict[str, Any]:
        """Validate the parsed command for safety and feasibility"""
        issues = []

        # Check for dangerous patterns
        if command.action == RobotActionType.UNKNOWN:
            issues.append("Could not determine command intent")

        # Check for missing critical information
        if command.target == "unknown" and command.action in [RobotActionType.GRASP, RobotActionType.FIND]:
            issues.append("Missing target object for manipulation command")

        # Check for conflicting parameters
        if 'location' in command.parameters and command.action == RobotActionType.STOP:
            issues.append("Location parameter not applicable for STOP command")

        return {
            'is_valid': len(issues) == 0,
            'issues': issues
        }

    async def _enhance_with_llm(self, parsed_command: ParsedCommand) -> ParsedCommand:
        """Enhance parsed command using LLM"""
        if not openai.api_key:
            # Try to get from environment
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                openai.api_key = api_key
            else:
                # Return original if no API key
                return parsed_command

        prompt = f"""
        You are a robot command enhancement system. Improve the following parsed command:

        Original Command: "{parsed_command.original_text}"
        Parsed Action: {parsed_command.action.value}
        Target: {parsed_command.target}
        Parameters: {json.dumps(parsed_command.parameters)}
        Entities: {json.dumps(parsed_command.entities)}

        Provide an enhanced version with:
        1. Improved confidence score if applicable
        2. Additional relevant parameters
        3. Better target identification
        4. Missing entities that should be considered
        5. Dependencies that should be tracked

        Return in JSON format:
        {{
            "action": "...",
            "target": "...",
            "parameters": {{...}},
            "confidence": 0.0-1.0,
            "entities": {{...}},
            "dependencies": [...],
            "reasoning": "..."
        }}
        """

        try:
            response = await openai.ChatCompletion.acreate(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500
            )

            enhanced_data = json.loads(response.choices[0].message.content)

            # Update the parsed command with enhanced data
            action_value = enhanced_data.get('action', parsed_command.action.value)
            action_enum = RobotActionType.UNKNOWN
            for action_type in RobotActionType:
                if action_type.value == action_value:
                    action_enum = action_type
                    break

            return ParsedCommand(
                action=action_enum,
                target=enhanced_data.get('target', parsed_command.target),
                parameters=enhanced_data.get('parameters', parsed_command.parameters),
                confidence=enhanced_data.get('confidence', parsed_command.confidence),
                original_text=parsed_command.original_text,
                entities=enhanced_data.get('entities', parsed_command.entities),
                dependencies=enhanced_data.get('dependencies', parsed_command.dependencies),
                status=parsed_command.status,  # Keep original status
                reasoning=enhanced_data.get('reasoning', parsed_command.reasoning)
            )

        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}")
            # Return original command if enhancement fails
            return parsed_command

    def parse_command_batch(self, commands: List[str]) -> List[ParseResult]:
        """Parse multiple commands in batch"""
        results = []
        for cmd in commands:
            result = self.parse_command(cmd)
            results.append(result)
        return results

    def parse_compound_command(self, compound_command: str) -> ParseResult:
        """
        Parse compound commands that contain multiple actions

        Args:
            compound_command: Command with multiple actions (e.g., "Go to kitchen and pick up the red cup")

        Returns:
            ParseResult with multiple commands
        """
        # Split compound command into sub-commands
        sub_commands = self._split_compound_command(compound_command)

        all_commands = []
        errors = []
        warnings = []
        total_confidence = 0.0
        success_count = 0

        for sub_cmd in sub_commands:
            result = self.parse_command(sub_cmd)
            if result.success:
                all_commands.extend(result.commands)
                total_confidence += result.confidence
                success_count += 1
            else:
                errors.extend(result.errors)

        overall_confidence = total_confidence / success_count if success_count > 0 else 0.0

        return ParseResult(
            success=len(all_commands) > 0,
            commands=all_commands,
            confidence=overall_confidence,
            errors=errors,
            warnings=warnings
        )

    def _split_compound_command(self, compound_command: str) -> List[str]:
        """Split compound command into sub-commands"""
        # Common connectors that indicate separate commands
        connectors = [r'\band\b', r'\bthen\b', r'\bnext\b', r'\bafter that\b', r'\bfollowed by\b']

        # Split by connectors
        import re
        parts = [compound_command]
        for connector in connectors:
            new_parts = []
            for part in parts:
                # Split and keep the split parts
                splits = re.split(connector, part, flags=re.IGNORECASE)
                new_parts.extend([s.strip() for s in splits if s.strip()])
            parts = new_parts

        # Clean up parts
        cleaned_parts = []
        for part in parts:
            # Remove connector words from the middle of commands
            for connector in connectors:
                part = re.sub(connector, '', part, flags=re.IGNORECASE).strip()
            if part:
                cleaned_parts.append(part)

        return cleaned_parts if cleaned_parts else [compound_command]


class CommandOptimizer:
    """
    Optimizer for parsed robot commands
    """

    def __init__(self):
        self.action_cost_map = {
            RobotActionType.NAVIGATE: 10,
            RobotActionType.GRASP: 5,
            RobotActionType.PLACE: 5,
            RobotActionType.FIND: 8,
            RobotActionType.DETECT: 3,
            RobotActionType.STOP: 1,
            RobotActionType.PAUSE: 1,
            RobotActionType.CONTINUE: 1
        }

    def optimize_command_sequence(self, commands: List[ParsedCommand]) -> List[ParsedCommand]:
        """
        Optimize a sequence of commands for efficiency

        Args:
            commands: List of parsed commands

        Returns:
            Optimized list of commands
        """
        if len(commands) <= 1:
            return commands

        # Simple optimization: group similar actions
        optimized = []
        i = 0

        while i < len(commands):
            current_cmd = commands[i]

            # Look for similar actions that can be combined
            if current_cmd.action == RobotActionType.NAVIGATE:
                # Check if next command is also navigation to nearby location
                if i + 1 < len(commands) and commands[i + 1].action == RobotActionType.NAVIGATE:
                    # In a real implementation, we'd check if locations are close
                    # For now, just keep them separate
                    optimized.append(current_cmd)
                    i += 1
                else:
                    optimized.append(current_cmd)
                    i += 1
            else:
                optimized.append(current_cmd)
                i += 1

        return optimized

    def calculate_command_efficiency(self, commands: List[ParsedCommand]) -> Dict[str, float]:
        """
        Calculate efficiency metrics for a command sequence

        Args:
            commands: List of parsed commands

        Returns:
            Efficiency metrics
        """
        if not commands:
            return {"efficiency": 0.0, "total_cost": 0, "action_count": 0}

        total_cost = 0
        for cmd in commands:
            cost = self.action_cost_map.get(cmd.action, 5)  # Default cost
            total_cost += cost

        # Efficiency is inversely proportional to cost
        efficiency = 100.0 / (1 + total_cost / len(commands)) if commands else 0.0

        return {
            "efficiency": efficiency,
            "total_cost": total_cost,
            "action_count": len(commands),
            "avg_cost_per_action": total_cost / len(commands) if commands else 0
        }


def main():
    """Example usage of the NLP Robot Parser"""
    print("NLP Robot Parser Example")

    # Initialize the parser
    parser = NLPRobotParser(use_llm_enhancement=False)  # Disable LLM for this example to avoid API calls

    # Example commands to test
    test_commands = [
        "Navigate to the kitchen",
        "Pick up the red cup from the table",
        "Go to the living room and find the blue book",
        "Place the object on the shelf",
        "Stop the robot",
        "Grasp the small green bottle",
        "Find the keys in the bedroom",
        "Move to the office and pick up the pen"
    ]

    print("\n--- Single Command Parsing Examples ---")
    for i, cmd in enumerate(test_commands):
        print(f"\nCommand {i+1}: '{cmd}'")
        result = parser.parse_command(cmd)

        if result.success and result.commands:
            parsed_cmd = result.commands[0]
            print(f"  Action: {parsed_cmd.action.value}")
            print(f"  Target: {parsed_cmd.target}")
            print(f"  Confidence: {parsed_cmd.confidence:.3f}")
            print(f"  Parameters: {parsed_cmd.parameters}")
            print(f"  Entities: {parsed_cmd.entities}")
            print(f"  Status: {parsed_cmd.status.value}")
            print(f"  Reasoning: {parsed_cmd.reasoning}")
        else:
            print(f"  Failed to parse: {result.errors}")

        if result.warnings:
            print(f"  Warnings: {result.warnings}")

    # Test compound command
    print(f"\n--- Compound Command Example ---")
    compound_cmd = "Go to the kitchen and pick up the red cup, then place it on the counter"
    print(f"Compound Command: '{compound_cmd}'")

    compound_result = parser.parse_compound_command(compound_cmd)
    if compound_result.success:
        print(f"  Parsed {len(compound_result.commands)} sub-commands:")
        for j, sub_cmd in enumerate(compound_result.commands):
            print(f"    {j+1}. Action: {sub_cmd.action.value}, Target: {sub_cmd.target}, Confidence: {sub_cmd.confidence:.3f}")

    # Test optimization
    print(f"\n--- Command Optimization Example ---")
    optimizer = CommandOptimizer()

    sample_commands = [
        ParsedCommand(
            action=RobotActionType.NAVIGATE,
            target="kitchen",
            parameters={"location": "kitchen"},
            confidence=0.9,
            original_text="go to kitchen",
            entities={"locations": ["kitchen"]},
            dependencies=[],
            status=CommandParsingStatus.SUCCESS,
            reasoning="Navigating to kitchen"
        ),
        ParsedCommand(
            action=RobotActionType.GRASP,
            target="cup",
            parameters={"object": "cup", "color": "red"},
            confidence=0.85,
            original_text="pick up red cup",
            entities={"objects": ["cup"], "colors": ["red"]},
            dependencies=[],
            status=CommandParsingStatus.SUCCESS,
            reasoning="Grasping red cup"
        )
    ]

    optimized = optimizer.optimize_command_sequence(sample_commands)
    efficiency = optimizer.calculate_command_efficiency(optimized)

    print(f"  Original commands: {len(sample_commands)}")
    print(f"  Optimized commands: {len(optimized)}")
    print(f"  Efficiency: {efficiency['efficiency']:.2f}%")
    print(f"  Total cost: {efficiency['total_cost']}")
    print(f"  Average cost per action: {efficiency['avg_cost_per_action']:.2f}")

    print("\nNLP Robot Parser example completed!")


if __name__ == "__main__":
    main()