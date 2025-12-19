---
id: 002
title: Security-First Constitution Update
stage: constitution
date: 2025-12-18
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: 004-vla-capstone
user: zohaib
command: /sp.constitution
labels: ["security", "constitution", "rag-chatbot", "cohere"]
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

Project: Physical AI \& Humanoid Robotics — Secure RAG Chatbot + Book Platform

Core principles:
- Security-first architecture
- Zero hardcoded secrets
- Grounded AI responses only
- Deterministic retrieval behavior
- Clear separation of frontend and backend trust boundaries

AI behavior rules:
- NEVER assume credentials exist
- ALWAYS request credentials explicitly if required
- NEVER embed secrets into code or prompts
- ALL credentials must be injected via environment variables

Security standards:
- Environment variable–only secret handling
- Fail-fast on missing secrets
- Frontend must never access secrets
- Backend validates secrets on startup
- Selection-only mode strictly isolated

Constraints:
- Embeddings: Cohere
- Vector DB: Qdrant Cloud
- Metadata DB: Neon Serverless Postgres
- Reasoning: OpenAI Agents / ChatKit
- Frontend: Docusaurus (React)
- Backend: FastAPI (Python)

Success criteria:
- No secret leakage
- Selection-only mode enforced
- Production-grade security posture

## Response snapshot

Updated constitution from v1.0.1 to v2.0.0 (MAJOR version bump) with:

1. **5 Core Principles**: Security-First Architecture, Zero Hardcoded Secrets, Grounded AI Responses Only, Deterministic Retrieval Behavior, Clear Trust Boundaries

2. **4 AI Behavior Rules**: Never assume credentials, always request explicitly, never embed secrets, all credentials via env vars

3. **5 Security Standards**: Environment variable-only handling, fail-fast on missing secrets, frontend isolation, backend validation, selection-only mode isolation

4. **Technology Constraints Table**: Cohere, Qdrant, Neon, OpenAI, Docusaurus, FastAPI locked as mandatory stack

5. **Success Criteria Checklists**: Security, Functional, Operational categories with testable checkboxes

## Outcome

- ✅ Impact: Major governance change - project now security-first with explicit AI behavior rules
- 🧪 Tests: Constitution validation passed - no unresolved placeholders
- 📁 Files: 1 file modified (.specify/memory/constitution.md)
- 🔁 Next prompts: Security audit of existing code against new standards
- 🧠 Reflection: MAJOR bump appropriate due to fundamental principle changes

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - All principles declarative and testable
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate existing backend code against new Security Standards
