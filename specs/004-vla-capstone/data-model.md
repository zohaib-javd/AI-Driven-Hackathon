# Data Model: Physical AI & Humanoid Robotics Book

## Overview
This document defines the key data entities and relationships for the Physical AI & Humanoid Robotics book project, including educational content, simulation examples, and the RAG chatbot system.

## Educational Content Entities

### 1. Module
- **Fields**:
  - id: string (e.g., "module-1-ros", "module-2-digital-twin", etc.)
  - title: string
  - description: string
  - target_audience: array of strings
  - prerequisites: array of strings
  - learning_objectives: array of strings
  - total_chapters: integer
  - estimated_completion_time: string
  - created_at: datetime
  - updated_at: datetime

- **Relationships**:
  - Has many: Chapter
  - Belongs to: Book

### 2. Chapter
- **Fields**:
  - id: string (e.g., "module-1-chapter-3")
  - module_id: string
  - title: string
  - description: string
  - word_count: integer
  - estimated_reading_time: string
  - learning_objectives: array of strings
  - prerequisites: array of strings
  - content_type: enum ("text", "code", "simulation", "exercise", "assessment")
  - difficulty_level: enum ("beginner", "intermediate", "advanced")
  - requires_simulation: boolean
  - simulation_environment: enum ("none", "gazebo", "isaac", "unity")
  - created_at: datetime
  - updated_at: datetime

- **Relationships**:
  - Belongs to: Module
  - Has many: CodeExample
  - Has many: Exercise
  - Has many: AssessmentQuestion

### 3. CodeExample
- **Fields**:
  - id: string
  - chapter_id: string
  - title: string
  - description: string
  - code_language: string (e.g., "python", "cpp", "bash")
  - code_content: string (markdown with syntax highlighting)
  - execution_environment: enum ("ros2", "gazebo", "isaac", "unity", "python", "other")
  - simulation_required: boolean
  - dependencies: array of strings
  - expected_output: string
  - validation_steps: array of strings
  - created_at: datetime
  - updated_at: datetime

- **Relationships**:
  - Belongs to: Chapter
  - Has many: ValidationTest

### 4. Exercise
- **Fields**:
  - id: string
  - chapter_id: string
  - title: string
  - description: string
  - difficulty_level: enum ("beginner", "intermediate", "advanced")
  - type: enum ("coding", "simulation", "theoretical", "practical")
  - estimated_completion_time: string
  - required_resources: array of strings
  - success_criteria: array of strings
  - hints: array of strings
  - solution: string (optional)
  - created_at: datetime
  - updated_at: datetime

- **Relationships**:
  - Belongs to: Chapter

### 5. AssessmentQuestion
- **Fields**:
  - id: string
  - chapter_id: string
  - question_text: string
  - question_type: enum ("multiple_choice", "short_answer", "practical", "essay")
  - difficulty_level: enum ("beginner", "intermediate", "advanced")
  - options: array of strings (for multiple choice)
  - correct_answer: string
  - explanation: string
  - tags: array of strings
  - created_at: datetime
  - updated_at: datetime

- **Relationships**:
  - Belongs to: Chapter

## Simulation and Robotics Entities

### 6. RobotModel (URDF)
- **Fields**:
  - id: string
  - name: string
  - description: string
  - urdf_content: string
  - sdf_content: string (for Gazebo)
  - joint_count: integer
  - link_count: integer
  - sensor_configurations: object
  - actuator_configurations: object
  - kinematic_chains: array of objects
  - created_at: datetime
  - updated_at: datetime

- **Relationships**:
  - Used by: SimulationEnvironment
  - Has many: RobotConfiguration

### 7. SimulationEnvironment
- **Fields**:
  - id: string
  - name: string
  - type: enum ("gazebo", "isaac", "unity", "custom")
  - version: string
  - description: string
  - supported_robot_formats: array of strings
  - physics_engine: string
  - rendering_engine: string
  - supported_sensors: array of strings
  - performance_requirements: object
  - created_at: datetime
  - updated_at: datetime

- **Relationships**:
  - Contains: RobotModel
  - Has many: SimulationScene
  - Has many: SimulationExample

### 8. SimulationScene
- **Fields**:
  - id: string
  - environment_id: string
  - name: string
  - description: string
  - scene_file_path: string
  - objects: array of objects
  - lighting_config: object
  - environment_config: object
  - physics_config: object
  - required_models: array of strings
  - created_at: datetime
  - updated_at: datetime

- **Relationships**:
  - Belongs to: SimulationEnvironment
  - Used by: Chapter

### 9. SimulationExample
- **Fields**:
  - id: string
  - chapter_id: string
  - environment_id: string
  - title: string
  - description: string
  - setup_steps: array of strings
  - execution_steps: array of strings
  - expected_behavior: string
  - troubleshooting_tips: array of strings
  - validation_criteria: array of strings
  - created_at: datetime
  - updated_at: datetime

- **Relationships**:
  - Belongs to: Chapter, SimulationEnvironment

## RAG Chatbot Entities

### 10. DocumentChunk
- **Fields**:
  - id: string
  - document_id: string
  - chunk_text: string
  - chunk_metadata: object
  - embedding: array of floats (vector)
  - page_number: integer
  - section_title: string
  - chapter_id: string
  - module_id: string
  - created_at: datetime
  - updated_at: datetime

- **Relationships**:
  - Belongs to: BookContent
  - Used by: RAGQuery

### 11. BookContent
- **Fields**:
  - id: string
  - content_type: enum ("module", "chapter", "section", "example")
  - content_id: string (references Module, Chapter, etc.)
  - title: string
  - content_text: string
  - metadata: object
  - created_at: datetime
  - updated_at: datetime

- **Relationships**:
  - Has many: DocumentChunk
  - Used by: RAGQuery

### 12. RAGQuery
- **Fields**:
  - id: string
  - query_text: string
  - query_embedding: array of floats (vector)
  - relevant_chunks: array of strings (chunk IDs)
  - response_text: string
  - grounding_accuracy: float (0-1)
  - source_documents: array of strings
  - timestamp: datetime
  - user_feedback: object (if provided)

- **Relationships**:
  - Uses: DocumentChunk
  - Related to: BookContent

## Validation and Testing Entities

### 13. ValidationTest
- **Fields**:
  - id: string
  - code_example_id: string
  - test_type: enum ("compilation", "execution", "simulation", "integration")
  - test_description: string
  - test_commands: array of strings
  - expected_results: object
  - validation_criteria: array of strings
  - environment_requirements: object
  - created_at: datetime
  - updated_at: datetime

- **Relationships**:
  - Belongs to: CodeExample

### 14. StudentProgress
- **Fields**:
  - id: string
  - student_id: string
  - chapter_id: string
  - completion_status: enum ("not_started", "in_progress", "completed")
  - completion_percentage: float (0-100)
  - time_spent: integer (seconds)
  - exercise_attempts: array of objects
  - assessment_scores: array of objects
  - last_accessed: datetime
  - created_at: datetime
  - updated_at: datetime

- **Relationships**:
  - Belongs to: Chapter
  - Related to: Student

## State Transitions

### Chapter State Transitions
- `draft` → `review` → `approved` → `published`
- `published` → `deprecated` (if outdated)

### CodeExample State Transitions
- `proposed` → `developed` → `tested` → `validated` → `published`
- `published` → `needs_update` → `deprecated`

### SimulationExample State Transitions
- `design` → `implementation` → `testing` → `validation` → `published`
- `published` → `deprecated` (if simulation environment changes)

## Validation Rules

### 1. Module Validation
- Must have 14+ chapters (for 4 modules = 50+ total)
- Estimated completion time must be provided
- Target audience must be specified
- Prerequisites must be defined

### 2. Chapter Validation
- Word count must be between 800-1500 words
- Learning objectives must be defined
- Content type must be specified
- Difficulty level must be assigned

### 3. CodeExample Validation
- Must have valid syntax for specified language
- Dependencies must be resolvable
- Expected output must be provided
- Validation steps must be defined

### 4. RobotModel Validation
- URDF must be well-formed XML
- Joint and link names must follow ROS conventions
- Kinematic chains must be valid
- Sensor configurations must be supported by target environments

### 5. DocumentChunk Validation
- Text length must be appropriate for embedding (not too long/short)
- Must reference valid book content
- Embedding must be generated successfully
- Metadata must be complete and accurate