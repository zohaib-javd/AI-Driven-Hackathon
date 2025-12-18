# Implementation Plan: Physical AI & Humanoid Robotics — Full Book

**Branch**: `004-vla-capstone` | **Date**: 2025-12-15 | **Spec**: [link to spec.md](spec.md)
**Input**: Feature specification from `/specs/004-vla-capstone/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create a complete, multi-module textbook (Docusaurus MDX) covering the entire embodied-AI pipeline: ROS 2 → Digital Twin Simulation → NVIDIA Isaac AI Brain → Vision-Language-Action Robotics. This includes 50+ Docusaurus chapters across 4 modules, a capstone autonomous humanoid agent, GitHub Pages deployment, and a RAG chatbot over the book content.

## Technical Context

**Language/Version**: Python 3.10+, JavaScript/TypeScript for web components, Markdown/MDX for documentation
**Primary Dependencies**: Docusaurus v3.x, ROS 2 Humble Hawksbill, NVIDIA Isaac Sim, Gazebo Garden, OpenAI API, FastAPI, Neon Postgres, Qdrant
**Storage**: Git repository for source content, Neon Postgres for RAG chatbot metadata, Qdrant for vector storage
**Testing**: pytest for Python components, Jest for JavaScript components, manual validation of educational content
**Target Platform**: GitHub Pages for book deployment, Ubuntu 22.04 for ROS 2 development, Windows/Linux for Isaac Sim
**Project Type**: Documentation + educational content + web application (RAG chatbot)
**Performance Goals**: <200ms response time for RAG chatbot, 90%+ grounding accuracy for book content, <3s page load time for Docusaurus
**Constraints**: All code examples must work in target environments (ROS 2 Humble, Gazebo Garden, Isaac Sim), model-agnostic LLM prompts, simulation-only (no hardware deployment)
**Scale/Scope**: 4 modules with 14+ chapters each (50+ total), 85% student satisfaction rate, 100% reproducible examples

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Technical Excellence**: All content must be grounded in official documentation and validated in real environments - PASS
- Code examples validated in ROS 2 Humble + Gazebo Garden + Isaac Sim environments
- Following official documentation for all frameworks

**Educational Clarity**: Complex concepts presented with clear learning objectives and practical examples - PASS
- Each chapter includes learning objectives, prerequisites, code examples, and exercises
- Following "Learn → Simulate → Deploy" pedagogy

**Reproducible Learning**: Every concept must be accompanied by executable code and simulation steps - PASS
- All examples tested in target environments
- Step-by-step execution instructions provided

**Modular Architecture**: Components designed for independent learning while maintaining cohesive flow - PASS
- Four distinct modules with clear boundaries
- Cross-references between related concepts

**Open Standards**: Following industry-standard frameworks and protocols - PASS
- Using ROS 2, Gazebo, Isaac Sim, Docusaurus - all industry standards
- OpenAI API integration for language understanding

## Project Structure

### Documentation (this feature)

```text
specs/004-vla-capstone/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
book/
├── docs/                    # Docusaurus MDX content for all 4 modules
│   ├── module-1-ros/        # Module 1: The Robotic Nervous System (ROS 2)
│   │   ├── chapter-1.mdx
│   │   ├── chapter-2.mdx
│   │   └── ...
│   ├── module-2-digital-twin/ # Module 2: The Digital Twin (Gazebo & Unity)
│   │   ├── chapter-1.mdx
│   │   ├── chapter-2.mdx
│   │   └── ...
│   ├── module-3-ai-brain/   # Module 3: The AI-Robot Brain (NVIDIA Isaac™)
│   │   ├── chapter-1.mdx
│   │   ├── chapter-2.mdx
│   │   └── ...
│   └── module-4-vla/        # Module 4: Vision-Language-Action (VLA)
│       ├── chapter-1.mdx
│       ├── chapter-2.mdx
│       └── ...
├── src/                     # Docusaurus custom components
│   ├── components/
│   └── pages/
├── docusaurus.config.js     # Docusaurus configuration
└── package.json             # Dependencies and build scripts

rag-chatbot/
├── app/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Data models
│   ├── routes/              # API routes
│   └── services/            # Business logic
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
└── docker-compose.yml       # Container configuration

simulation-examples/
├── ros-examples/            # ROS 2 examples from Module 1
├── gazebo-examples/         # Gazebo examples from Module 2
├── isaac-examples/          # Isaac Sim examples from Module 3
└── vla-examples/            # VLA examples from Module 4

docusaurus/
├── docs/
├── src/
└── static/
```

**Structure Decision**: Multi-component structure with separate directories for book content, RAG chatbot, and simulation examples. The book uses Docusaurus for web deployment, the RAG chatbot uses FastAPI with Neon Postgres and Qdrant, and simulation examples are organized by module.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
