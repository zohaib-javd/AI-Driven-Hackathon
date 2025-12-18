# Tasks: Physical AI & Humanoid Robotics — Full Book

**Branch**: `004-vla-capstone` | **Date**: 2025-12-17 | **Spec**: Cross-module master task list
**Input**: All module specifications (001-004) + Master plan + User task outline

## Overview

This task list defines all implementation work required to build the complete 53-chapter Physical AI & Humanoid Robotics textbook with integrated RAG chatbot, ready for GitHub Pages deployment.

**Success Criteria**:
- All 4 modules written in MDX and validated in Docusaurus
- All simulation and code examples reproducible
- Capstone agent completes: **Voice → Plan → Navigate → Perceive → Manipulate**
- RAG Chatbot answers book questions with 90%+ grounding accuracy
- GitHub Pages site publicly accessible

---

## Task Status Legend

- `[ ]` - Not started
- `[~]` - In progress
- `[x]` - Completed
- `[!]` - Blocked

---

# PHASE 0: GLOBAL INFRASTRUCTURE

## Global-1: Create Docusaurus Project Structure

**Priority**: P0 (Blocker for all content)
**Dependencies**: None
**Estimated Effort**: Medium

### Tasks

- [ ] **Global-1.1**: Initialize Docusaurus with classic template
  - **File**: `physical-ai-humanoid-robotics/`
  - **Command**: `npx create-docusaurus@latest physical-ai-humanoid-robotics classic --typescript`
  - **Acceptance**: Project builds with `npm run build`

- [ ] **Global-1.2**: Create module folder structure
  - **Files**:
    - `docs/intro.mdx`
    - `docs/glossary.mdx`
    - `docs/module-1-ros2/_category_.json`
    - `docs/module-2-digital-twin/_category_.json`
    - `docs/module-3-isaac/_category_.json`
    - `docs/module-4-vla/_category_.json`
  - **Acceptance**: All folders created with category metadata

- [ ] **Global-1.3**: Configure `sidebars.ts` navigation
  - **File**: `sidebars.ts`
  - **Content**: Four module categories with chapter ordering
  - **Acceptance**: Sidebar shows all 4 modules with placeholder chapters

- [ ] **Global-1.4**: Update `docusaurus.config.ts` with book metadata
  - **File**: `docusaurus.config.ts`
  - **Content**:
    - Title: "Physical AI & Humanoid Robotics"
    - Tagline: "From ROS 2 to Vision-Language-Action Robots"
    - GitHub Pages deployment config
    - Code syntax highlighting (Python, YAML, XML, bash, TypeScript)
  - **Acceptance**: Site title and metadata display correctly

- [ ] **Global-1.5**: Set up GitHub Actions deployment workflow
  - **File**: `.github/workflows/deploy.yml`
  - **Content**: Build on PR, deploy to GitHub Pages on merge to main
  - **Acceptance**: Workflow triggers on push/PR

---

## Global-2: Apply Unified Book Style

**Priority**: P0 (Required for consistent content)
**Dependencies**: Global-1
**Estimated Effort**: Medium

### Tasks

- [ ] **Global-2.1**: Create custom MDX components
  - **Files**:
    - `src/components/LearningObjectives/index.tsx`
    - `src/components/CodeExample/index.tsx`
    - `src/components/DiagramDescription/index.tsx`
    - `src/components/Exercise/index.tsx`
    - `src/components/MCQ/index.tsx`
  - **Acceptance**: Components render correctly in MDX files

- [ ] **Global-2.2**: Configure custom CSS styling
  - **File**: `src/css/custom.css`
  - **Content**: Book theme colors, code block styling, component styles
  - **Acceptance**: Consistent visual appearance across all pages

- [ ] **Global-2.3**: Create global glossary
  - **File**: `docs/glossary.mdx`
  - **Content**: Terms from ROS 2, simulation, AI, VLA domains
  - **Categories**: ROS 2, Gazebo, Unity, Isaac, Navigation, VLA, General AI
  - **Acceptance**: All key terms defined with cross-references

- [ ] **Global-2.4**: Set MDX formatting standards document
  - **File**: `CONTRIBUTING.md`
  - **Content**: Code block styles, component usage, terminology guidelines
  - **Acceptance**: Style guide available for content authors

- [ ] **Global-2.5**: Update landing page
  - **File**: `src/pages/index.tsx`
  - **Content**: Module cards, prerequisites, getting started guide
  - **Acceptance**: Landing page shows book overview with module navigation

---

## Global-3: Create RAG Integration Plumbing

**Priority**: P1 (Parallel to content)
**Dependencies**: Global-1
**Estimated Effort**: Large

### Tasks

- [ ] **Global-3.1**: Set up FastAPI backend skeleton
  - **Directory**: `rag-chatbot/`
  - **Files**:
    - `src/main.py` - FastAPI application
    - `src/config.py` - Environment configuration
    - `requirements.txt` - Python dependencies
  - **Acceptance**: Server starts with health endpoint

- [ ] **Global-3.2**: Connect to Neon Serverless Postgres
  - **File**: `rag-chatbot/src/services/database.py`
  - **Content**: Connection pool, metadata storage
  - **Acceptance**: Database connection established, tables created

- [ ] **Global-3.3**: Initialize Qdrant vector database
  - **File**: `rag-chatbot/src/services/vectorstore.py`
  - **Content**: Collection creation, embedding storage
  - **Acceptance**: Collection exists, test embedding stored/retrieved

- [ ] **Global-3.4**: Prepare MDX ingestion pipeline
  - **Files**:
    - `rag-chatbot/scripts/ingest_book.py`
    - `rag-chatbot/src/services/embeddings.py`
  - **Content**: MDX parsing, chunking, embedding generation
  - **Acceptance**: Sample MDX file ingested with chunks in Qdrant

- [ ] **Global-3.5**: Configure OpenAI Agent for book Q&A
  - **Files**:
    - `rag-chatbot/src/services/agent.py`
    - `rag-chatbot/src/services/retrieval.py`
  - **Content**: RAG retrieval, grounded responses, citation
  - **Acceptance**: Agent answers test question with book citation

- [ ] **Global-3.6**: Build chat API endpoints
  - **Files**:
    - `rag-chatbot/src/api/chat.py`
    - `rag-chatbot/src/api/ingest.py`
  - **Endpoints**: `POST /chat`, `GET /search`, `POST /ingest`
  - **Acceptance**: All endpoints respond correctly

- [ ] **Global-3.7**: Create Docker deployment
  - **Files**:
    - `rag-chatbot/Dockerfile`
    - `rag-chatbot/docker-compose.yml`
  - **Acceptance**: Container builds and runs

---

## Global-4: Create Hands-On Project Templates

**Priority**: P1 (Required before module content)
**Dependencies**: Global-1
**Estimated Effort**: Medium

### Tasks

- [ ] **Global-4.1**: Create ROS 2 workspace template
  - **Directory**: `static/code/ros2_ws/`
  - **Content**: Package structure, CMakeLists.txt, setup.py templates
  - **Acceptance**: Workspace builds with `colcon build`

- [ ] **Global-4.2**: Create Gazebo simulation starter
  - **Directory**: `static/code/module-2/gazebo_worlds/`
  - **Content**: Empty world, basic humanoid spawn script
  - **Acceptance**: World loads in Gazebo Garden

- [ ] **Global-4.3**: Create Unity HDRP template project
  - **Directory**: `static/code/module-2/unity_robotics/`
  - **Content**: Project settings, ROS-TCP-Connector setup
  - **Acceptance**: Project opens in Unity 2022 LTS

- [ ] **Global-4.4**: Create Isaac Sim sample scene
  - **Directory**: `static/code/module-3/isaac_scenes/`
  - **Content**: Basic humanoid scene with ROS 2 bridge
  - **Acceptance**: Scene loads in Isaac Sim with ROS 2 topics

---

# PHASE 1: MODULE 1 — THE ROBOTIC NERVOUS SYSTEM (ROS 2)

**Module Specs**: `specs/001-ros2-nervous-system/spec.md`
**Chapter Count**: 13
**Dependencies**: Global-1, Global-2

## Module-1 Content Tasks

- [ ] **1-1**: Write Module 1 introduction
  - **File**: `docs/module-1-ros2/01-what-is-ros2.mdx`
  - **Word Count**: 800-1500
  - **Content**: ROS 2 as nervous system, middleware concept, ecosystem overview
  - **Components**: `<LearningObjectives>`, `<DiagramDescription>`
  - **Acceptance**: Chapter renders, explains ROS 2 purpose clearly

- [ ] **1-2**: Explain ROS 2 architecture + DDS
  - **File**: `docs/module-1-ros2/02-dds-architecture.mdx`
  - **Word Count**: 800-1500
  - **Content**: DDS middleware, QoS profiles, discovery mechanism
  - **Components**: `<LearningObjectives>`, `<DiagramDescription>`
  - **Acceptance**: Student understands DDS communication model

- [ ] **1-3**: Create Node examples (Python / rclpy)
  - **File**: `docs/module-1-ros2/03-ros2-nodes.mdx`
  - **Word Count**: 800-1500
  - **Content**: Node creation, lifecycle states, composition
  - **Code Examples**:
    - `static/code/module-1/minimal_node.py`
    - `static/code/module-1/lifecycle_node.py`
  - **Acceptance**: Code runs, node appears in `ros2 node list`

- [ ] **1-4**: Create Topic pub-sub exercises
  - **File**: `docs/module-1-ros2/04-topics-pubsub.mdx`
  - **Word Count**: 800-1500
  - **Content**: Publishers, subscribers, message types, QoS
  - **Code Examples**:
    - `static/code/module-1/talker.py`
    - `static/code/module-1/listener.py`
    - `static/code/module-1/custom_msg/`
  - **Acceptance**: Messages flow between nodes, visible with `ros2 topic echo`

- [ ] **1-5**: Show Services & Actions with sample robot task
  - **File**: `docs/module-1-ros2/05-services-actions.mdx`
  - **Word Count**: 800-1500
  - **Content**: Request/response, long-running tasks, feedback
  - **Code Examples**:
    - `static/code/module-1/add_service.py`
    - `static/code/module-1/fibonacci_action.py`
  - **Acceptance**: Service responds, action sends feedback

- [ ] **1-6**: Add Parameters, Launch files, configs
  - **File**: `docs/module-1-ros2/06-parameters-config.mdx`
  - **Word Count**: 800-1500
  - **Content**: Parameter declaration, YAML config, runtime updates
  - **Code Examples**:
    - `static/code/module-1/param_node.py`
    - `static/code/module-1/config.yaml`
  - **Acceptance**: Parameters read from YAML, updated with `ros2 param set`

- [ ] **1-7**: Create Launch files for humanoid
  - **File**: `docs/module-1-ros2/07-launch-files.mdx`
  - **Word Count**: 800-1500
  - **Content**: Python launch system, arguments, conditions, groups
  - **Code Examples**:
    - `static/code/module-1/humanoid_launch.py`
  - **Acceptance**: Launch file starts multiple nodes correctly

- [ ] **1-8**: Document rclpy integration with AI agents
  - **File**: `docs/module-1-ros2/08-rclpy-basics.mdx`
  - **Word Count**: 800-1500
  - **Content**: rclpy API patterns, callbacks, timers, multi-threading
  - **Code Examples**:
    - `static/code/module-1/rclpy_patterns.py`
  - **Acceptance**: All rclpy patterns demonstrated with working code

- [ ] **1-9**: Teach URDF fundamentals + links/joints
  - **File**: `docs/module-1-ros2/09-urdf-introduction.mdx`
  - **Word Count**: 800-1500
  - **Content**: Links, joints, visual/collision geometry, inertia
  - **Code Examples**:
    - `static/code/module-1/simple_arm.urdf`
  - **Acceptance**: URDF passes `check_urdf` validation

- [ ] **1-10**: Build humanoid URDF skeleton
  - **File**: `docs/module-1-ros2/10-humanoid-urdf.mdx`
  - **Word Count**: 800-1500
  - **Content**: Full humanoid model, kinematic chains, TF tree
  - **Code Examples**:
    - `static/code/module-1/humanoid.urdf`
  - **Acceptance**: Complete humanoid URDF loads in RViz

- [ ] **1-11**: Visualize robot in RViz tutorial
  - **File**: `docs/module-1-ros2/11-rviz-visualization.mdx`
  - **Word Count**: 800-1500
  - **Content**: TF tree, joint_state_publisher, RViz configuration
  - **Code Examples**:
    - `static/code/module-1/visualize.launch.py`
    - `static/code/module-1/rviz_config.rviz`
  - **Acceptance**: Robot displays in RViz with movable joints

- [ ] **1-12**: Mini-project: Control humanoid joints
  - **File**: `docs/module-1-ros2/12-mini-project-joint-control.mdx`
  - **Word Count**: 800-1500
  - **Content**: Joint control with Python, closed-loop feedback
  - **Code Examples**:
    - `static/code/module-1/joint_controller.py`
    - `static/code/module-1/joint_control_launch.py`
  - **Acceptance**: Student controls arm joints via Python script

- [ ] **1-13**: Add MCQs, Summary, Review Exercises
  - **File**: `docs/module-1-ros2/13-summary-assessment.mdx`
  - **Word Count**: 800-1500
  - **Content**: 20 MCQs, 5 exercises, module summary
  - **Components**: `<MCQ>`, `<Exercise>`
  - **Acceptance**: All questions have correct answers, exercises are completable

**Module 1 Completion Output**: Students able to operate a ROS 2 robot skeleton + control joints.

---

# PHASE 2: MODULE 2 — THE DIGITAL TWIN (GAZEBO & UNITY)

**Module Specs**: `specs/002-digital-twin-sim/spec.md`
**Chapter Count**: 13
**Dependencies**: Module 1 completion

## Module-2 Content Tasks

- [ ] **2-1**: Write Module 2 intro: Digital Twins
  - **File**: `docs/module-2-digital-twin/01-what-is-digital-twin.mdx`
  - **Word Count**: 800-1500
  - **Content**: Virtual replica concept, sim-to-real, industry applications
  - **Components**: `<LearningObjectives>`, `<DiagramDescription>`
  - **Acceptance**: Student understands digital twin value proposition

- [ ] **2-2**: Explain Gazebo physics engine
  - **File**: `docs/module-2-digital-twin/02-gazebo-overview.mdx`
  - **Word Count**: 800-1500
  - **Content**: Physics engines (DART, ODE), worlds, plugins
  - **Code Examples**:
    - `static/code/module-2/empty_world.sdf`
  - **Acceptance**: Student understands Gazebo architecture

- [ ] **2-3**: Import humanoid URDF into Gazebo
  - **File**: `docs/module-2-digital-twin/03-urdf-to-gazebo.mdx`
  - **Word Count**: 800-1500
  - **Content**: SDF conversion, model spawning, inspection
  - **Code Examples**:
    - `static/code/module-2/spawn_humanoid.launch.py`
  - **Acceptance**: Humanoid loads in Gazebo without errors

- [ ] **2-4**: Tune physics: collisions, mass, inertia
  - **File**: `docs/module-2-digital-twin/04-physics-simulation.mdx`
  - **Word Count**: 800-1500
  - **Content**: Mass distribution, friction, collision geometry
  - **Code Examples**:
    - `static/code/module-2/physics_config.yaml`
  - **Acceptance**: Robot has stable, realistic physics behavior

- [ ] **2-5**: Create Gazebo world + lighting + materials
  - **File**: `docs/module-2-digital-twin/05-environment-building.mdx`
  - **Word Count**: 800-1500
  - **Content**: Ground planes, obstacles, lighting, visual materials
  - **Code Examples**:
    - `static/code/module-2/indoor_world.sdf`
  - **Acceptance**: Furnished room environment loads correctly

- [ ] **2-6**: Add LiDAR, Depth Camera, IMU simulations
  - **File**: `docs/module-2-digital-twin/06-sensor-simulation.mdx`
  - **Word Count**: 800-1500
  - **Content**: Sensor plugins, noise models, coordinate frames
  - **Code Examples**:
    - `static/code/module-2/sensor_plugins.urdf`
  - **Acceptance**: All sensor types publish data in Gazebo

- [ ] **2-7**: Connect sensors to ROS 2 subscriber nodes
  - **File**: `docs/module-2-digital-twin/07-ros2-sensor-integration.mdx`
  - **Word Count**: 800-1500
  - **Content**: Gazebo-ROS bridge, topic mapping, QoS
  - **Code Examples**:
    - `static/code/module-2/sensor_subscriber.py`
  - **Acceptance**: Sensor data visible in RViz, processed by ROS 2 nodes

- [ ] **2-8**: Introduce Unity for robotics
  - **File**: `docs/module-2-digital-twin/08-unity-for-robotics.mdx`
  - **Word Count**: 800-1500
  - **Content**: Unity architecture, robotics packages, setup
  - **Code Examples**:
    - Unity project setup instructions
  - **Acceptance**: Unity project created with robotics packages

- [ ] **2-9**: Build HDRP high-fidelity environment
  - **File**: `docs/module-2-digital-twin/09-unity-hdrp-rendering.mdx`
  - **Word Count**: 800-1500
  - **Content**: HDRP lighting, PBR materials, post-processing
  - **Code Examples**:
    - `static/code/module-2/unity_scenes/hdrp_setup.md`
  - **Acceptance**: Photorealistic scene renders in Unity

- [ ] **2-10**: Teach human-robot interaction in Unity
  - **File**: `docs/module-2-digital-twin/10-human-robot-interaction.mdx`
  - **Word Count**: 800-1500
  - **Content**: Animated characters, proximity detection, interaction
  - **Code Examples**:
    - `static/code/module-2/unity_scripts/HRIController.cs`
  - **Acceptance**: Robot-human interaction scenario works

- [ ] **2-11**: Connect Unity with ROS 2 (ROS-Unity bridge)
  - **File**: `docs/module-2-digital-twin/11-ros-unity-bridge.mdx`
  - **Word Count**: 800-1500
  - **Content**: ROS-TCP-Connector, message definitions, pub/sub
  - **Code Examples**:
    - `static/code/module-2/unity_bridge.py`
    - `static/code/module-2/unity_scripts/ROSConnection.cs`
  - **Acceptance**: Joint commands from ROS 2 control Unity robot

- [ ] **2-12**: Mini-project: Full digital twin
  - **File**: `docs/module-2-digital-twin/12-mini-project-digital-twin.mdx`
  - **Word Count**: 800-1500
  - **Content**: Complete pipeline: ROS 2 → Gazebo → Unity
  - **Code Examples**:
    - `static/code/module-2/digital_twin_launch.py`
  - **Acceptance**: Synchronized digital twin across all systems

- [ ] **2-13**: Add MCQs, Summary, Simulation Tasks
  - **File**: `docs/module-2-digital-twin/13-summary-assessment.mdx`
  - **Word Count**: 800-1500
  - **Content**: 25 MCQs, 5 simulation challenges, module summary
  - **Components**: `<MCQ>`, `<Exercise>`
  - **Acceptance**: All assessments completable

**Module 2 Completion Output**: Students simulate sensors + build interactive environments.

---

# PHASE 3: MODULE 3 — THE AI-ROBOT BRAIN (NVIDIA ISAAC)

**Module Specs**: `specs/003-isaac-ai-brain/spec.md`
**Chapter Count**: 13
**Dependencies**: Module 1, Module 2 completion

## Module-3 Content Tasks

- [ ] **3-1**: Write Module 3 intro: AI-driven robotics
  - **File**: `docs/module-3-isaac/01-isaac-sim-overview.mdx`
  - **Word Count**: 800-1500
  - **Content**: Why photorealistic simulation, sim-to-real, synthetic data
  - **Components**: `<LearningObjectives>`, `<DiagramDescription>`
  - **Acceptance**: Student understands Isaac Sim value proposition

- [ ] **3-2**: Install & configure NVIDIA Isaac Sim
  - **File**: `docs/module-3-isaac/02-isaac-setup.mdx`
  - **Word Count**: 800-1500
  - **Content**: Installation, GPU requirements, ROS 2 bridge setup
  - **Code Examples**:
    - `static/code/module-3/isaac_launch.sh`
  - **Acceptance**: Isaac Sim launches with ROS 2 bridge active

- [ ] **3-3**: Import humanoid URDF into Isaac + ROS Bridge
  - **File**: `docs/module-3-isaac/03-importing-robots.mdx`
  - **Word Count**: 800-1500
  - **Content**: URDF to USD conversion, action graphs, joint publishers
  - **Code Examples**:
    - `static/code/module-3/urdf_import.py`
  - **Acceptance**: Humanoid in Isaac Sim controlled via ROS 2

- [ ] **3-4**: Configure photorealistic rendering & materials
  - **File**: `docs/module-3-isaac/04-photorealistic-rendering.mdx`
  - **Word Count**: 800-1500
  - **Content**: PBR materials, lighting, ray tracing, HDR
  - **Code Examples**:
    - `static/code/module-3/material_setup.py`
  - **Acceptance**: Scene renders with photorealistic quality

- [ ] **3-5**: Generate synthetic vision datasets
  - **File**: `docs/module-3-isaac/05-synthetic-data-generation.mdx`
  - **Word Count**: 800-1500
  - **Content**: Replicator, domain randomization, output formats
  - **Code Examples**:
    - `static/code/module-3/data_generation.py`
  - **Acceptance**: RGB, depth, segmentation, bounding boxes generated

- [ ] **3-6**: Explain Isaac ROS architecture
  - **File**: `docs/module-3-isaac/06-isaac-ros-overview.mdx`
  - **Word Count**: 800-1500
  - **Content**: GPU acceleration, perception nodes, integration
  - **Components**: `<LearningObjectives>`, `<DiagramDescription>`
  - **Acceptance**: Student understands Isaac ROS benefits

- [ ] **3-7**: Implement VSLAM pipeline, verify pose tracking
  - **File**: `docs/module-3-isaac/07-isaac-ros-vslam.mdx`
  - **Word Count**: 800-1500
  - **Content**: Stereo vision, feature tracking, pose estimation
  - **Code Examples**:
    - `static/code/module-3/vslam_config.yaml`
    - `static/code/module-3/vslam_launch.py`
  - **Acceptance**: VSLAM tracks robot pose accurately

- [ ] **3-8**: Integrate perception nodes (AprilTags, stereo, depth)
  - **File**: `docs/module-3-isaac/08-isaac-ros-perception.mdx`
  - **Word Count**: 800-1500
  - **Content**: Fiducial detection, stereo matching, depth estimation
  - **Code Examples**:
    - `static/code/module-3/perception_pipeline.py`
  - **Acceptance**: Multiple perception nodes run together

- [ ] **3-9**: Explain Nav2 stack: mapping → planning → control
  - **File**: `docs/module-3-isaac/09-nav2-overview.mdx`
  - **Word Count**: 800-1500
  - **Content**: Behavior trees, costmaps, planners, controllers
  - **Components**: `<LearningObjectives>`, `<DiagramDescription>`
  - **Acceptance**: Student understands Nav2 architecture

- [ ] **3-10**: Configure Nav2 components
  - **File**: `docs/module-3-isaac/10-nav2-architecture.mdx`
  - **Word Count**: 800-1500
  - **Content**: Map server, planner, controller, recovery configuration
  - **Code Examples**:
    - `static/code/module-3/nav2_params.yaml`
  - **Acceptance**: Nav2 configured for humanoid robot

- [ ] **3-11**: Connect Nav2 + Isaac ROS for humanoid navigation
  - **File**: `docs/module-3-isaac/11-isaac-ros-nav2-integration.mdx`
  - **Word Count**: 800-1500
  - **Content**: Odometry fusion, localization, goal management
  - **Code Examples**:
    - `static/code/module-3/nav2_isaac_launch.py`
  - **Acceptance**: Robot navigates using VSLAM odometry

- [ ] **3-12**: Mini-project: Humanoid walks through obstacle course
  - **File**: `docs/module-3-isaac/12-mini-project-obstacle-course.mdx`
  - **Word Count**: 800-1500
  - **Content**: Complete navigation system, testing, debugging
  - **Code Examples**:
    - `static/code/module-3/obstacle_course/`
  - **Acceptance**: Humanoid navigates obstacle course autonomously

- [ ] **3-13**: Add MCQs, Summary, Navigation Tasks
  - **File**: `docs/module-3-isaac/13-summary-assessment.mdx`
  - **Word Count**: 800-1500
  - **Content**: 30 MCQs, 5 navigation challenges, module summary
  - **Components**: `<MCQ>`, `<Exercise>`
  - **Acceptance**: All assessments completable

**Module 3 Completion Output**: Students build GPU-accelerated AI brain using Isaac + VSLAM + Nav2.

---

# PHASE 4: MODULE 4 — VISION-LANGUAGE-ACTION (VLA)

**Module Specs**: `specs/004-vla-capstone/spec.md`
**Chapter Count**: 14
**Dependencies**: Module 1, Module 2, Module 3 completion

## Module-4 Content Tasks

- [ ] **4-1**: Write Module 4 intro: The VLA paradigm
  - **File**: `docs/module-4-vla/01-what-is-vla.mdx`
  - **Word Count**: 800-1500
  - **Content**: Cognitive robotics, embodied AI, language-grounded action
  - **Components**: `<LearningObjectives>`, `<DiagramDescription>`
  - **Acceptance**: Student understands VLA concept

- [ ] **4-2**: Describe Voice → Language → Action pipeline
  - **File**: `docs/module-4-vla/02-vla-pipeline.mdx`
  - **Word Count**: 800-1500
  - **Content**: Data flow, component interfaces, system integration
  - **Components**: `<DiagramDescription>` (pipeline diagram)
  - **Acceptance**: Student can diagram complete VLA flow

- [ ] **4-3**: Integrate Whisper for speech-to-text robot commands
  - **File**: `docs/module-4-vla/03-whisper-voice-commands.mdx`
  - **Word Count**: 800-1500
  - **Content**: Audio processing, transcription, streaming
  - **Code Examples**:
    - `static/code/module-4/whisper_node.py`
  - **Acceptance**: Voice commands transcribed with >90% accuracy

- [ ] **4-4**: Build natural language → structured task parser
  - **File**: `docs/module-4-vla/04-natural-language-parsing.mdx`
  - **Word Count**: 800-1500
  - **Content**: Intent extraction, slot filling, command structure
  - **Code Examples**:
    - `static/code/module-4/command_parser.py`
  - **Acceptance**: Commands parsed into action/object/location

- [ ] **4-5**: Implement LLM cognitive planner
  - **File**: `docs/module-4-vla/05-llm-cognitive-planning.mdx`
  - **Word Count**: 800-1500
  - **Content**: Prompt engineering, action generation, model-agnostic design
  - **Code Examples**:
    - `static/code/module-4/llm_planner.py`
    - `static/code/module-4/prompts/planning_prompt.txt`
  - **Acceptance**: LLM generates valid ROS 2 action sequences

- [ ] **4-6**: Add safety guardrails for LLM-controlled robots
  - **File**: `docs/module-4-vla/06-safety-guardrails.mdx`
  - **Word Count**: 800-1500
  - **Content**: Action validation, workspace limits, emergency stop
  - **Code Examples**:
    - `static/code/module-4/safety_validator.py`
  - **Acceptance**: Unsafe commands rejected with explanation

- [ ] **4-7**: Connect perception models for object selection
  - **File**: `docs/module-4-vla/07-perception-integration.mdx`
  - **Word Count**: 800-1500
  - **Content**: Object detection, segmentation, pose estimation
  - **Code Examples**:
    - `static/code/module-4/perception_node.py`
  - **Acceptance**: Objects detected with bounding boxes and poses

- [ ] **4-8**: Implement object selection and manipulation planning
  - **File**: `docs/module-4-vla/08-object-selection-manipulation.mdx`
  - **Word Count**: 800-1500
  - **Content**: Object selection from detections, grasp planning
  - **Code Examples**:
    - `static/code/module-4/grasp_planner.py`
  - **Acceptance**: Correct object selected, valid grasp computed

- [ ] **4-9**: Integrate Nav2 for LLM-generated navigation routes
  - **File**: `docs/module-4-vla/09-navigation-llm-plans.mdx`
  - **Word Count**: 800-1500
  - **Content**: Goal translation, navigation monitoring, spatial reasoning
  - **Code Examples**:
    - `static/code/module-4/nav_executor.py`
  - **Acceptance**: Robot navigates to LLM-specified locations

- [ ] **4-10**: Implement manipulation tasks
  - **File**: `docs/module-4-vla/10-manipulator-control.mdx`
  - **Word Count**: 800-1500
  - **Content**: Grasp execution, force control, pick-and-place
  - **Code Examples**:
    - `static/code/module-4/manipulator.py`
  - **Acceptance**: Robot performs pick-and-place operations

- [ ] **4-11**: Build full VLA agent loop
  - **File**: `docs/module-4-vla/11-vla-agent-loop.mdx`
  - **Word Count**: 800-1500
  - **Content**: State machine, component coordination, error handling
  - **Code Examples**:
    - `static/code/module-4/vla_agent.py`
  - **Acceptance**: Autonomous loop runs: listen → plan → execute

- [ ] **4-12**: Capstone: Autonomous Humanoid
  - **File**: `docs/module-4-vla/12-capstone-autonomous-humanoid.mdx`
  - **Word Count**: 1200-2000 (larger capstone chapter)
  - **Content**: Complete system integration, end-to-end demonstration
  - **Subcomponents**:
    - Voice command input
    - Planning the sequence
    - Navigating obstacles
    - Detecting and selecting objects
    - Performing manipulation actions
  - **Code Examples**:
    - `static/code/module-4/capstone/` (complete system)
  - **Acceptance**: Voice command → complete task execution

- [ ] **4-13**: Testing, metrics, and failure analysis
  - **File**: `docs/module-4-vla/13-testing-failure-modes.mdx`
  - **Word Count**: 800-1500
  - **Content**: Test design, metrics collection, root cause analysis
  - **Code Examples**:
    - `static/code/module-4/test_framework.py`
  - **Acceptance**: Test suite runs, metrics captured

- [ ] **4-14**: Add MCQs, Summary, Capstone Review
  - **File**: `docs/module-4-vla/14-summary-assessment.mdx`
  - **Word Count**: 800-1500
  - **Content**: 35 MCQs, 6 practical challenges, module summary
  - **Components**: `<MCQ>`, `<Exercise>`
  - **Acceptance**: All assessments completable

**Module 4 Completion Output**: Students create a fully autonomous voice-driven humanoid agent.

---

# PHASE 5: CROSS-MODULE INTEGRATION

**Dependencies**: All module content complete

## Integration Tasks

- [ ] **Int-1**: Create unified glossary with all terms
  - **File**: `docs/glossary.mdx`
  - **Content**: All ROS 2, simulation, AI, VLA terms consolidated
  - **Acceptance**: Every technical term has definition

- [ ] **Int-2**: Add cross-references between chapters
  - **Files**: All chapter MDX files
  - **Content**: "See Module X, Chapter Y" links where relevant
  - **Acceptance**: No broken internal links

- [ ] **Int-3**: Create book introduction
  - **File**: `docs/intro.mdx`
  - **Content**: Target audience, prerequisites, how to use book, setup guide
  - **Acceptance**: New reader can get started

- [ ] **Int-4**: Validate all code examples
  - **Environment**: ROS 2 Humble, Ubuntu 22.04, Isaac Sim
  - **Process**: Run each code example, verify output
  - **Acceptance**: 100% of code examples execute

- [ ] **Int-5**: Review chapter flow and prerequisites
  - **Process**: Verify progressive difficulty, no circular dependencies
  - **Acceptance**: Clear learning path from intro to capstone

---

# PHASE 6: CAPSTONE INTEGRATION

**Dependencies**: Phase 5 complete

## Capstone Tasks

- [ ] **Cap-1**: Build unified simulation (ROS 2 + Gazebo/Isaac)
  - **Files**: `static/code/capstone/unified_sim/`
  - **Content**: Single launch for complete simulation environment
  - **Acceptance**: All components start and communicate

- [ ] **Cap-2**: Implement full VLA pipeline in simulation
  - **Files**: `static/code/capstone/vla_pipeline/`
  - **Content**: Voice → Plan → Navigate → Perceive → Manipulate
  - **Acceptance**: Pipeline completes end-to-end

- [ ] **Cap-3**: Evaluate system on complex user commands
  - **Files**: `static/code/capstone/test_scenarios/`
  - **Content**: 10 test scenarios with varying complexity
  - **Acceptance**: 80%+ success rate on test scenarios

- [ ] **Cap-4**: Prepare final documentation in Docusaurus
  - **Files**: Capstone chapter and related documentation
  - **Acceptance**: Complete documentation of capstone system

- [ ] **Cap-5**: Index all content for RAG chatbot
  - **Script**: `rag-chatbot/scripts/ingest_book.py`
  - **Acceptance**: All 53 chapters indexed in Qdrant

- [ ] **Cap-6**: Deploy GitHub Pages site + RAG backend
  - **GitHub Pages**: Static site deployed
  - **RAG Backend**: API deployed to Vercel/Railway
  - **Acceptance**: Public URLs accessible

---

# PHASE 7: DEPLOYMENT & POLISH

**Dependencies**: Phase 6 complete

## Deployment Tasks

- [ ] **Deploy-1**: Finalize Docusaurus build
  - Remove sample content
  - Configure SEO metadata
  - Add social cards
  - **Acceptance**: Production build succeeds

- [ ] **Deploy-2**: Deploy to GitHub Pages
  - Configure custom domain (optional)
  - Set up HTTPS
  - Test all links
  - **Acceptance**: Site publicly accessible

- [ ] **Deploy-3**: Deploy RAG chatbot
  - Docker containerization
  - Deploy to Vercel/Railway
  - Configure CORS for book site
  - **Acceptance**: Chatbot responds to queries

- [ ] **Deploy-4**: Final validation
  - All 53 chapters render correctly
  - All code examples have syntax highlighting
  - RAG chatbot achieves 90%+ grounding accuracy
  - Capstone demo documented end-to-end
  - **Acceptance**: All success criteria met

---

## Task Summary

| Phase | Tasks | Status |
|-------|-------|--------|
| Global Infrastructure | 21 | Not Started |
| Module 1 (ROS 2) | 13 | Not Started |
| Module 2 (Digital Twin) | 13 | Not Started |
| Module 3 (Isaac) | 13 | Not Started |
| Module 4 (VLA) | 14 | Not Started |
| Cross-Module Integration | 5 | Not Started |
| Capstone Integration | 6 | Not Started |
| Deployment & Polish | 4 | Not Started |
| **Total** | **89** | Not Started |

---

## Dependency Graph

```
Global-1 (Docusaurus Setup)
    ├── Global-2 (Styling)
    ├── Global-3 (RAG Backend)
    └── Global-4 (Templates)
         │
         ▼
Module 1 (ROS 2) ──────────────────┐
         │                          │
         ▼                          │
Module 2 (Digital Twin) ───────────┤
         │                          │
         ▼                          │
Module 3 (Isaac) ──────────────────┤
         │                          │
         ▼                          │
Module 4 (VLA) ────────────────────┘
         │
         ▼
Cross-Module Integration
         │
         ▼
Capstone Integration
         │
         ▼
Deployment & Polish
```

---

## Next Steps

1. Begin with **Global-1.1**: Initialize Docusaurus project
2. Work through Global infrastructure in parallel where possible
3. Start Module 1 content after Global-2 styling is complete
4. RAG backend (Global-3) can proceed in parallel with content

---

**Generated**: 2025-12-17
**Spec Reference**: `specs/000-full-book-plan/plan.md`
