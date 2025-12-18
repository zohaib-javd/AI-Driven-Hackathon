"""
RAG Configuration for Vision-Language-Action (VLA) Module

This configuration defines how the RAG system will index and retrieve
information specific to the VLA module content.
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class RAGConfig:
    """Configuration for the RAG system"""

    # OpenAI API Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    embedding_model: str = "text-embedding-3-large"
    chat_model: str = "gpt-4-turbo"

    # Qdrant Configuration
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_collection_name: str = "vla_module_content"

    # Neon Postgres Configuration
    neon_connection_string: str = os.getenv("NEON_CONNECTION_STRING", "")

    # Embedding Configuration
    embedding_dimensions: int = 3072  # For text-embedding-3-large
    similarity_threshold: float = 0.7
    top_k: int = 5

    # Document Processing
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_document_length: int = 16000  # Max context length for models

    # Module-specific settings
    module_id: str = "module-4-vla"
    module_name: str = "Vision-Language-Action (VLA)"
    module_topics: List[str] = (
        "vision-language-action",
        "whisper-api",
        "llm-planning",
        "robotics-control",
        "perception-navigation",
        "manipulation",
        "voice-to-action",
        "cognitive-planning",
        "safety-guardrails",
        "vla-pipeline"
    )

    # Indexing configuration
    index_modules: List[str] = ["module-4-vla"]
    exclude_patterns: List[str] = [
        "test",
        "tests",
        "__pycache__",
        ".git",
        "node_modules",
        ".vscode",
        ".pytest_cache"
    ]

    # Search configuration
    search_weights: Dict[str, float] = {
        "title": 2.0,
        "content": 1.0,
        "code": 1.5,
        "diagram": 1.2
    }

    # Safety configuration
    safety_threshold: float = 0.8
    enable_safety_filter: bool = True
    safety_model: str = "text-moderation-latest"

    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable must be set")

        if not self.neon_connection_string:
            raise ValueError("NEON_CONNECTION_STRING environment variable must be set")

# Default configuration instance
DEFAULT_CONFIG = RAGConfig()

# Topic-specific query rewriters for VLA module
TOPIC_QUERY_REWRITERS = {
    "whisper": [
        "OpenAI Whisper",
        "speech recognition",
        "voice to text",
        "audio processing",
        "voice commands"
    ],
    "llm_planning": [
        "cognitive planning",
        "task breakdown",
        "action sequences",
        "reasoning pipeline",
        "natural language processing"
    ],
    "perception": [
        "object detection",
        "computer vision",
        "image segmentation",
        "sensor fusion",
        "environment perception"
    ],
    "navigation": [
        "path planning",
        "Nav2",
        "robot navigation",
        "waypoint following",
        "obstacle avoidance"
    ],
    "manipulation": [
        "grasping",
        "pick and place",
        "end effector control",
        "motion planning",
        "robotic arm control"
    ],
    "safety": [
        "safety constraints",
        "guardrails",
        "validation",
        "safety checks",
        "safe robot operation"
    ]
}

# Semantic chunking patterns specific to VLA content
SEMANTIC_CHUNKING_PATTERNS = [
    # Code blocks should be kept together
    r'```.*?```',
    # LaTeX equations should be kept together
    r'\$\$.*?\$\$',
    # Mermaid diagrams should be kept together
    r'```mermaid.*?```',
    # Headers and their following content
    r'#{1,6}.*?(?=\n#{1,6}|$)',
    # List items with their sub-items
    r'(\s*[-*]\s.*\n)+',
    # ROS message definitions
    r'(\w+)\s+(\w+)\s*',
    # Python function definitions
    r'def\s+\w+\s*\([^)]*\):.*?(?=\n\S|\Z)',
    # ROS launch file sections
    r'<[^>]*>.*?</[^>]*>',
]

# VLA-specific prompt templates
VLA_PROMPT_TEMPLATES = {
    "voice_command_to_action": {
        "system": "You are a robotics expert helping to convert voice commands into structured robot actions. The robot follows a Vision-Language-Action pipeline: Voice → Language → Reasoning → Action. Map natural language commands to specific robot behaviors.",
        "user": "Convert this voice command to structured robot actions: '{command}'. Provide a step-by-step plan with specific ROS 2 actions."
    },
    "perception_to_action": {
        "system": "You are a robotics expert helping to connect perception outputs to appropriate actions. Given what the robot perceives, determine the appropriate next actions.",
        "user": "The robot perceives: '{perception}'. What action should the robot take next? Consider safety constraints and task objectives."
    },
    "safety_validation": {
        "system": "You are a safety validation system for LLM-controlled robots. Assess whether the proposed robot action is safe and appropriate.",
        "user": "Validate this robot action: '{action}'. Is it safe to execute? Consider physical constraints, environment, and safety protocols."
    },
    "task_breakdown": {
        "system": "You are a task decomposition expert for humanoid robots. Break down high-level commands into executable steps.",
        "user": "Break down this high-level task: '{task}' into specific, executable steps for a humanoid robot with arms, legs, and sensors."
    }
}

def get_config() -> RAGConfig:
    """Get the RAG configuration instance"""
    return DEFAULT_CONFIG