"""
LLM Prompt Templates for Different Robot Tasks in VLA Pipeline

This module provides model-agnostic prompt templates for various robot tasks,
compatible with OpenAI, Claude, and LLaMA models. The templates follow a
structured format to ensure consistent output for the VLA pipeline.

Each template is designed to work with the cognitive planning system and
generates structured outputs suitable for ROS 2 action sequence generation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
import json


class RobotTaskType(Enum):
    """Enumeration of different robot task types."""
    NAVIGATION = "navigation"
    MANIPULATION = "manipulation"
    PERCEPTION = "perception"
    COMPOSITE = "composite"
    SAFETY_CHECK = "safety_check"


class TaskDifficulty(Enum):
    """Enumeration of task difficulty levels."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class PromptTemplate:
    """Dataclass representing a prompt template."""
    name: str
    task_type: RobotTaskType
    difficulty: TaskDifficulty
    system_prompt: str
    user_prompt: str
    output_format: str
    examples: Optional[List[Dict[str, str]]] = None
    constraints: Optional[List[str]] = None


class LLMPromptTemplates:
    """Collection of LLM prompt templates for different robot tasks."""

    def __init__(self):
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize all prompt templates."""
        templates = {}

        # Navigation templates
        templates["nav_basic"] = PromptTemplate(
            name="Basic Navigation",
            task_type=RobotTaskType.NAVIGATION,
            difficulty=TaskDifficulty.BASIC,
            system_prompt=(
                "You are a navigation planner for a humanoid robot. "
                "Convert natural language navigation commands into structured navigation goals. "
                "Output must be in JSON format with specific fields."
            ),
            user_prompt=(
                "Command: {command}\n"
                "Environment: {environment}\n"
                "Current position: {current_position}\n\n"
                "Convert this navigation command into a structured navigation goal. "
                "Provide coordinates (x, y, z) and orientation (roll, pitch, yaw) for the destination. "
                "Include any safety considerations and obstacle avoidance instructions."
            ),
            output_format=(
                "Output JSON format:\n"
                "{\n"
                "  \"navigation_goal\": {\n"
                "    \"destination\": {\"x\": float, \"y\": float, \"z\": float},\n"
                "    \"orientation\": {\"roll\": float, \"pitch\": float, \"yaw\": float},\n"
                "    \"waypoints\": [{\"x\": float, \"y\": float, \"z\": float}],\n"
                "    \"safety_considerations\": [\"string\"],\n"
                "    \"obstacle_avoidance\": [\"string\"]\n"
                "  }\n"
                "}"
            ),
            examples=[
                {
                    "input": "Navigate to the kitchen door",
                    "output": (
                        '{\n'
                        '  "navigation_goal": {\n'
                        '    "destination": {"x": 5.2, "y": 3.1, "z": 0.0},\n'
                        '    "orientation": {"roll": 0.0, "pitch": 0.0, "yaw": 1.57},\n'
                        '    "waypoints": [{"x": 2.0, "y": 1.5, "z": 0.0}],\n'
                        '    "safety_considerations": ["Avoid obstacles", "Maintain safe distance"],\n'
                        '    "obstacle_avoidance": ["Dynamic obstacle detection", "Path replanning"]\n'
                        '  }\n'
                        '}'
                    )
                }
            ],
            constraints=[
                "Output must be valid JSON",
                "Include all required fields",
                "Consider robot kinematics",
                "Respect safety constraints"
            ]
        )

        templates["nav_complex"] = PromptTemplate(
            name="Complex Navigation",
            task_type=RobotTaskType.NAVIGATION,
            difficulty=TaskDifficulty.ADVANCED,
            system_prompt=(
                "You are a sophisticated navigation planner for a humanoid robot. "
                "Handle complex navigation tasks involving multiple destinations, "
                "dynamic obstacles, and time constraints. "
                "Output must be in structured JSON format."
            ),
            user_prompt=(
                "Command: {command}\n"
                "Environment: {environment}\n"
                "Current position: {current_position}\n"
                "Time constraints: {time_constraints}\n"
                "Known obstacles: {obstacles}\n\n"
                "Generate a complex navigation plan with multiple waypoints, "
                "considering all constraints and dynamic factors. "
                "Include priority levels for different parts of the journey."
            ),
            output_format=(
                "Output JSON format:\n"
                "{\n"
                "  \"complex_navigation_plan\": {\n"
                "    \"primary_destination\": {\"x\": float, \"y\": float, \"z\": float},\n"
                "    \"secondary_destinations\": [{\"x\": float, \"y\": float, \"z\": float}],\n"
                "    \"waypoints\": [\n"
                "      {\n"
                "        \"position\": {\"x\": float, \"y\": float, \"z\": float},\n"
                "        \"orientation\": {\"roll\": float, \"pitch\": float, \"yaw\": float},\n"
                "        \"priority\": int,\n"
                "        \"duration_estimate\": float\n"
                "      }\n"
                "    ],\n"
                "    \"safety_protocols\": [\"string\"],\n"
                "    \"contingency_plans\": [\"string\"]\n"
                "  }\n"
                "}"
            ),
            examples=[
                {
                    "input": "Go to the kitchen, then to the living room, avoiding the moving robot in the hallway",
                    "output": (
                        '{\n'
                        '  "complex_navigation_plan": {\n'
                        '    "primary_destination": {"x": 5.2, "y": 3.1, "z": 0.0},\n'
                        '    "secondary_destinations": [{"x": 8.0, "y": 1.5, "z": 0.0}],\n'
                        '    "waypoints": [\n'
                        '      {\n'
                        '        "position": {"x": 2.0, "y": 1.5, "z": 0.0},\n'
                        '        "orientation": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},\n'
                        '        "priority": 1,\n'
                        '        "duration_estimate": 30.0\n'
                        '      }\n'
                        '    ],\n'
                        '    "safety_protocols": ["Dynamic obstacle detection", "Safe distance maintenance"],\n'
                        '    "contingency_plans": ["Alternative route to kitchen"]\n'
                        '  }\n'
                        '}'
                    )
                }
            ],
            constraints=[
                "Output must be valid JSON",
                "Include all required fields",
                "Consider dynamic obstacles",
                "Optimize path efficiency",
                "Maintain safety protocols"
            ]
        )

        # Manipulation templates
        templates["manip_basic"] = PromptTemplate(
            name="Basic Manipulation",
            task_type=RobotTaskType.MANIPULATION,
            difficulty=TaskDifficulty.BASIC,
            system_prompt=(
                "You are a manipulation planner for a humanoid robot. "
                "Convert natural language manipulation commands into structured grasp and placement actions. "
                "Output must be in JSON format with specific fields."
            ),
            user_prompt=(
                "Command: {command}\n"
                "Object: {object_description}\n"
                "Environment: {environment}\n"
                "Robot capabilities: {capabilities}\n\n"
                "Convert this manipulation command into a structured action sequence. "
                "Include grasp pose, placement pose, and any safety considerations."
            ),
            output_format=(
                "Output JSON format:\n"
                "{\n"
                "  \"manipulation_sequence\": {\n"
                "    \"object_id\": \"string\",\n"
                "    \"grasp_pose\": {\n"
                "      \"position\": {\"x\": float, \"y\": float, \"z\": float},\n"
                "      \"orientation\": {\"roll\": float, \"pitch\": float, \"yaw\": float}\n"
                "    },\n"
                "    \"placement_pose\": {\n"
                "      \"position\": {\"x\": float, \"y\": float, \"z\": float},\n"
                "      \"orientation\": {\"roll\": float, \"pitch\": float, \"yaw\": float}\n"
                "    },\n"
                "    \"gripper_configuration\": \"string\",\n"
                "    \"safety_considerations\": [\"string\"]\n"
                "  }\n"
                "}"
            ),
            examples=[
                {
                    "input": "Pick up the red cup and place it on the table",
                    "output": (
                        '{\n'
                        '  "manipulation_sequence": {\n'
                        '    "object_id": "red_cup_001",\n'
                        '    "grasp_pose": {\n'
                        '      "position": {"x": 1.2, "y": 0.5, "z": 0.8},\n'
                        '      "orientation": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0}\n'
                        '    },\n'
                        '    "placement_pose": {\n'
                        '      "position": {"x": 1.5, "y": 0.5, "z": 0.8},\n'
                        '      "orientation": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0}\n'
                        '    },\n'
                        '    "gripper_configuration": "precision_pinch",\n'
                        '    "safety_considerations": ["Fragile object handling", "Collision avoidance"]\n'
                        '  }\n'
                        '}'
                    )
                }
            ],
            constraints=[
                "Output must be valid JSON",
                "Include all required fields",
                "Consider object properties",
                "Respect robot limitations",
                "Ensure safety during manipulation"
            ]
        )

        templates["manip_complex"] = PromptTemplate(
            name="Complex Manipulation",
            task_type=RobotTaskType.MANIPULATION,
            difficulty=TaskDifficulty.ADVANCED,
            system_prompt=(
                "You are a sophisticated manipulation planner for a humanoid robot. "
                "Handle complex manipulation tasks involving multiple objects, "
                "assembly operations, or multi-step processes. "
                "Output must be in structured JSON format."
            ),
            user_prompt=(
                "Command: {command}\n"
                "Objects: {object_list}\n"
                "Environment: {environment}\n"
                "Assembly requirements: {assembly_specs}\n"
                "Robot capabilities: {capabilities}\n\n"
                "Generate a complex manipulation sequence with multiple steps, "
                "considering all assembly requirements and object relationships."
            ),
            output_format=(
                "Output JSON format:\n"
                "{\n"
                "  \"complex_manipulation_sequence\": {\n"
                "    \"steps\": [\n"
                "      {\n"
                "        \"step_id\": int,\n"
                "        \"action_type\": \"string\",\n"
                "        \"target_objects\": [\"string\"],\n"
                "        \"poses\": [\n"
                "          {\n"
                "            \"position\": {\"x\": float, \"y\": float, \"z\": float},\n"
                "            \"orientation\": {\"roll\": float, \"pitch\": float, \"yaw\": float}\n"
                "          }\n"
                "        ],\n"
                "        \"gripper_configurations\": [\"string\"],\n"
                "        \"constraints\": [\"string\"]\n"
                "      }\n"
                "    ],\n"
                "    \"assembly_result\": \"string\",\n"
                "    \"verification_steps\": [\"string\"]\n"
                "  }\n"
                "}"
            ),
            examples=[
                {
                    "input": "Assemble the toy car by placing the wheels on the chassis",
                    "output": (
                        '{\n'
                        '  "complex_manipulation_sequence": {\n'
                        '    "steps": [\n'
                        '      {\n'
                        '        "step_id": 1,\n'
                        '        "action_type": "grasp",\n'
                        '        "target_objects": ["wheel_front_left"],\n'
                        '        "poses": [\n'
                        '          {\n'
                        '            "position": {"x": 0.5, "y": 0.3, "z": 0.2},\n'
                        '            "orientation": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0}\n'
                        '          }\n'
                        '        ],\n'
                        '        "gripper_configurations": ["cylindrical_grasp"],\n'
                        '        "constraints": ["Gentle grip", "Precise alignment"]\n'
                        '      }\n'
                        '    ],\n'
                        '    "assembly_result": "toy_car_assembled",\n'
                        '    "verification_steps": ["Check wheel attachment", "Verify stability"]\n'
                        '  }\n'
                        '}'
                    )
                }
            ],
            constraints=[
                "Output must be valid JSON",
                "Include all required fields",
                "Consider assembly order",
                "Ensure structural integrity",
                "Verify completion criteria"
            ]
        )

        # Perception templates
        templates["perception_basic"] = PromptTemplate(
            name="Basic Perception",
            task_type=RobotTaskType.PERCEPTION,
            difficulty=TaskDifficulty.BASIC,
            system_prompt=(
                "You are a perception analyzer for a humanoid robot. "
                "Process sensor data and identify objects in the environment. "
                "Output must be in JSON format with specific fields."
            ),
            user_prompt=(
                "Sensor data: {sensor_data}\n"
                "Environment: {environment}\n"
                "Query: {query}\n\n"
                "Analyze the sensor data and identify objects matching the query. "
                "Provide object positions, properties, and confidence scores."
            ),
            output_format=(
                "Output JSON format:\n"
                "{\n"
                "  \"perception_results\": {\n"
                "    \"detected_objects\": [\n"
                "      {\n"
                "        \"object_id\": \"string\",\n"
                "        \"category\": \"string\",\n"
                "        \"position\": {\"x\": float, \"y\": float, \"z\": float},\n"
                "        \"confidence\": float,\n"
                "        \"properties\": {\"color\": \"string\", \"size\": \"string\"}\n"
                "      }\n"
                "    ],\n"
                "    \"environment_map\": \"string\",\n"
                "    \"quality_assessment\": \"string\"\n"
                "  }\n"
                "}"
            ),
            examples=[
                {
                    "input": "Find all red objects in the room",
                    "output": (
                        '{\n'
                        '  "perception_results": {\n'
                        '    "detected_objects": [\n'
                        '      {\n'
                        '        "object_id": "red_ball_001",\n'
                        '        "category": "ball",\n'
                        '        "position": {"x": 2.1, "y": 1.5, "z": 0.3},\n'
                        '        "confidence": 0.95,\n'
                        '        "properties": {"color": "red", "size": "small"}\n'
                        '      }\n'
                        '    ],\n'
                        '    "environment_map": "room_layout_map_001",\n'
                        '    "quality_assessment": "high"\n'
                        '  }\n'
                        '}'
                    )
                }
            ],
            constraints=[
                "Output must be valid JSON",
                "Include all required fields",
                "Provide confidence scores",
                "Accurate positioning",
                "Consistent object categorization"
            ]
        )

        # Composite task templates
        templates["composite_task"] = PromptTemplate(
            name="Composite Task Planning",
            task_type=RobotTaskType.COMPOSITE,
            difficulty=TaskDifficulty.ADVANCED,
            system_prompt=(
                "You are a composite task planner for a humanoid robot. "
                "Break down complex tasks into sequences of navigation, manipulation, and perception actions. "
                "Output must be in structured JSON format with temporal dependencies."
            ),
            user_prompt=(
                "Command: {command}\n"
                "Environment: {environment}\n"
                "Constraints: {constraints}\n"
                "Capabilities: {capabilities}\n\n"
                "Create a comprehensive plan that combines navigation, manipulation, and perception. "
                "Include temporal dependencies, resource allocation, and error recovery strategies."
            ),
            output_format=(
                "Output JSON format:\n"
                "{\n"
                "  \"composite_plan\": {\n"
                "    \"task_sequence\": [\n"
                "      {\n"
                "        \"action_id\": int,\n"
                "        \"action_type\": \"navigation|manipulation|perception|composite\",\n"
                "        \"description\": \"string\",\n"
                "        \"dependencies\": [int],\n"
                "        \"resources\": [\"string\"],\n"
                "        \"estimated_duration\": float\n"
                "      }\n"
                "    ],\n"
                "    \"resource_allocation\": {\"grippers\": [], \"sensors\": [], \"navigation\": []},\n"
                "    \"error_recovery\": [\"string\"],\n"
                "    \"success_criteria\": [\"string\"]\n"
                "  }\n"
                "}"
            ),
            examples=[
                {
                    "input": "Go to the kitchen, find a cup, pick it up, and bring it to the living room",
                    "output": (
                        '{\n'
                        '  "composite_plan": {\n'
                        '    "task_sequence": [\n'
                        '      {\n'
                        '        "action_id": 1,\n'
                        '        "action_type": "navigation",\n'
                        '        "description": "Navigate to kitchen",\n'
                        '        "dependencies": [],\n'
                        '        "resources": ["navigation_system"],\n'
                        '        "estimated_duration": 45.0\n'
                        '      },\n'
                        '      {\n'
                        '        "action_id": 2,\n'
                        '        "action_type": "perception",\n'
                        '        "description": "Detect cup in kitchen",\n'
                        '        "dependencies": [1],\n'
                        '        "resources": ["vision_system"],\n'
                        '        "estimated_duration": 20.0\n'
                        '      }\n'
                        '    ],\n'
                        '    "resource_allocation": {\n'
                        '      "grippers": ["left_arm_gripper"],\n'
                        '      "sensors": ["rgb_camera", "depth_sensor"],\n'
                        '      "navigation": ["nav2_stack"]\n'
                        '    },\n'
                        '    "error_recovery": ["Return to previous location if cup not found"],\n'
                        '    "success_criteria": ["Cup successfully transported to living room"]\n'
                        '  }\n'
                        '}'
                    )
                }
            ],
            constraints=[
                "Output must be valid JSON",
                "Include all required fields",
                "Consider temporal dependencies",
                "Optimize resource allocation",
                "Include error recovery strategies"
            ]
        )

        # Safety check templates
        templates["safety_check"] = PromptTemplate(
            name="Safety Validation",
            task_type=RobotTaskType.SAFETY_CHECK,
            difficulty=TaskDifficulty.INTERMEDIATE,
            system_prompt=(
                "You are a safety validator for a humanoid robot. "
                "Analyze proposed actions for potential safety violations and risks. "
                "Output must be in JSON format with safety assessments and recommendations."
            ),
            user_prompt=(
                "Proposed action: {action}\n"
                "Environment: {environment}\n"
                "Safety constraints: {constraints}\n"
                "Robot state: {robot_state}\n\n"
                "Evaluate the proposed action for safety compliance. "
                "Identify potential risks and provide safety recommendations."
            ),
            output_format=(
                "Output JSON format:\n"
                "{\n"
                "  \"safety_assessment\": {\n"
                "    \"compliance_status\": \"pass|warning|fail\",\n"
                "    \"identified_risks\": [\"string\"],\n"
                "    \"risk_level\": \"low|medium|high|critical\",\n"
                "    \"recommendations\": [\"string\"],\n"
                "    \"override_conditions\": [\"string\"]\n"
                "  }\n"
                "}"
            ),
            examples=[
                {
                    "input": "Move arm to position (2.0, 1.5, 0.8) near fragile objects",
                    "output": (
                        '{\n'
                        '  "safety_assessment": {\n'
                        '    "compliance_status": "warning",\n'
                        '    "identified_risks": ["Potential collision with fragile objects"],\n'
                        '    "risk_level": "medium",\n'
                        '    "recommendations": ["Reduce speed", "Activate collision detection"],\n'
                        '    "override_conditions": ["Emergency situation", "Supervisor approval"]\n'
                        '  }\n'
                        '}'
                    )
                }
            ],
            constraints=[
                "Output must be valid JSON",
                "Include all required fields",
                "Accurate risk assessment",
                "Practical recommendations",
                "Clear override conditions"
            ]
        )

        return templates

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Retrieve a specific prompt template by name."""
        return self.templates.get(name)

    def get_templates_by_type(self, task_type: RobotTaskType) -> List[PromptTemplate]:
        """Retrieve all templates of a specific task type."""
        return [template for template in self.templates.values()
                if template.task_type == task_type]

    def get_templates_by_difficulty(self, difficulty: TaskDifficulty) -> List[PromptTemplate]:
        """Retrieve all templates of a specific difficulty level."""
        return [template for template in self.templates.values()
                if template.difficulty == difficulty]

    def format_prompt(self, template_name: str, **kwargs) -> tuple[str, str]:
        """
        Format a prompt with provided arguments.

        Args:
            template_name: Name of the template to use
            **kwargs: Arguments to substitute in the prompt

        Returns:
            Tuple of (system_prompt, user_prompt) with substitutions applied
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        system_prompt = template.system_prompt
        user_prompt = template.user_prompt.format(**kwargs)

        return system_prompt, user_prompt


class ModelAgnosticFormatter:
    """Utility class for formatting prompts for different LLM models."""

    @staticmethod
    def format_for_openai(system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
        """Format prompts for OpenAI API."""
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

    @staticmethod
    def format_for_claude(system_prompt: str, user_prompt: str) -> str:
        """Format prompts for Claude API."""
        return f"{system_prompt}\n\nHuman: {user_prompt}\n\nAssistant:"

    @staticmethod
    def format_for_llama(system_prompt: str, user_prompt: str) -> str:
        """Format prompts for Llama models."""
        return f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{user_prompt} [/INST]"

    @staticmethod
    def format_for_generic(system_prompt: str, user_prompt: str) -> str:
        """Generic prompt formatting."""
        return f"System: {system_prompt}\nUser: {user_prompt}"


def get_default_prompt_templates() -> LLMPromptTemplates:
    """Get the default collection of LLM prompt templates."""
    return LLMPromptTemplates()


# Example usage
if __name__ == "__main__":
    # Initialize the prompt templates
    prompt_manager = get_default_prompt_templates()

    # Example: Get a navigation template and format it
    nav_template = prompt_manager.get_template("nav_basic")
    if nav_template:
        print(f"Template: {nav_template.name}")
        print(f"Task Type: {nav_template.task_type.value}")
        print(f"System Prompt: {nav_template.system_prompt[:100]}...")
        print(f"Output Format: {nav_template.output_format[:100]}...")

    # Example: Format a prompt for a specific task
    try:
        sys_prompt, usr_prompt = prompt_manager.format_prompt(
            "nav_basic",
            command="Go to the kitchen",
            environment="Living room with obstacles",
            current_position="Living room center"
        )

        print("\nFormatted Prompts:")
        print(f"System: {sys_prompt}")
        print(f"User: {usr_prompt}")

        # Format for different models
        openai_formatted = ModelAgnosticFormatter.format_for_openai(sys_prompt, usr_prompt)
        print(f"\nOpenAI Format: {openai_formatted}")

    except ValueError as e:
        print(f"Error: {e}")