---
id: 001
title: Physical AI Robotics Constitution Update
stage: constitution
date: 2025-12-16
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: 004-vla-capstone
user: Zohaib
command: /sp.constitution
labels: ["constitution", "physical-ai", "robotics", "governance"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - null
---

## Prompt

/sp.constitution

Project: Physical AI & Humanoid Robotics — Full Book + Integrated RAG Chatbot

Core principles:
- Technical accuracy based on robotics, AI, and simulation frameworks (ROS 2, Gazebo, Unity, NVIDIA Isaac)
- Clarity for both intermediate and advanced learners in robotics and embodied AI
- Hands-on reproducibility through executable code, simulations, and project pipelines
- Cohesive book structure using Docusaurus + Spec-Kit Plus conventions
- Modular architecture enabling integration with Claude Code and structured specs

Key standards:
- All robotics and AI claims must reference official documentation (ROS 2, NVIDIA Isaac, Gazebo, Unity, OpenAI, etc.)
- Code samples must be validated in ROS 2 Humble + Gazebo Garden + Isaac Sim environments
- Explanations must follow "learn → simulate → deploy" pedagogy
- Book output must follow Docusaurus MDX structure compatible with GitHub Pages
- RAG Chatbot must follow OpenAI Agents/ChatKit SDK + FastAPI + Neon Postgres + Qdrant stack
- Terminology must stay consistent across modules (ROS graph, namespaces, URDF, digital twin, VLA models)

Constraints:
- Four modules, each 8–12 chapters (minimum 40 total chapters)
- Each chapter must include:
    - Learning objectives
    - Code examples
    - Simulation steps
    - At least one robotics diagram or flow explanation
- Capstone must detail the end-to-end pipeline:
    Voice → LLM Planning → ROS 2 Actions → Navigation → Perception → Manipulation
- All MDX must be exportable to GitHub Pages without breaking builds
- All specs must be reusable inside Claude Code for automated editing

Success criteria:
- Entire book compiles successfully in Docusaurus and deploys on GitHub Pages
- Each module forms a coherent learning path: ROS → Simulation → Isaac → VLA
- All code tested or validated via Spec-Kit Plus or Claude Code execution sandbox
- RAG Chatbot answers questions using book content with 90%+ grounding accuracy
- Final capstone robot completes a full Voice-to-Action task in simulation

## Response snapshot

Updated constitution from v1.0.0 to v1.0.1 (PATCH). Key changes:
- Strengthened language from "should" to "MUST" for declarative, testable principles
- Added explicit RAG Chatbot Stack section under Technology Stack
- Added Documentation Reference Standards as Technical Principle #4
- Enhanced Governance section with formal Amendment Procedure and Compliance Review
- Added Sync Impact Report as HTML comment for tracking changes
- Verified compatibility with all dependent templates (plan, spec, tasks)

## Outcome

- ✅ Impact: Constitution updated and version bumped to 1.0.1
- 🧪 Tests: Template consistency verified across plan, spec, and tasks templates
- 📁 Files: .specify/memory/constitution.md updated
- 🔁 Next prompts: Consider /sp.spec for feature specifications, /sp.plan for implementation planning
- 🧠 Reflection: Existing constitution already captured user intent; refinements made principles more declarative and testable

## Evaluation notes (flywheel)

- Failure modes observed: None - constitution already aligned with user requirements
- Graders run and results (PASS/FAIL): PASS - All principles testable, no unresolved placeholders
- Prompt variant (if applicable): Standard /sp.constitution execution
- Next experiment (smallest change to try): N/A - constitution baseline established
