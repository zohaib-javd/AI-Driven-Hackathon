---
id: 003
title: Secure RAG Chatbot Task Generation
stage: tasks
date: 2025-12-19
surface: agent
model: claude-sonnet-4-5-20250929
feature: 005-secure-rag-chatbot
branch: 005-secure-rag-chatbot
user: zohaib
command: /sp.tasks
labels: ["tasks", "security", "rag-chatbot", "implementation", "cohere", "qdrant"]
links:
  spec: specs/005-secure-rag-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-secure-rag-chatbot/tasks.md
tests:
  - null
---

## Prompt

/sp.task

Generate a detailed task list for the Secure Dynamic RAG Chatbot feature.

SECURITY TASKS (NON-OPTIONAL):
- Ask user for credentials when needed
- Never accept credentials inline
- Move any detected hardcoded secret into `.env`
- Regenerate code after refactor

BACKEND TASKS:
- FastAPI server
- Secret validation on startup
- Cohere embeddings
- Qdrant vector search
- Neon DB integration

FRONTEND TASKS:
- Chat UI
- Text selection listener
- Mode indicator
- Error handling

VALIDATION TASKS:
- Refuse startup without secrets
- Refuse answers without context
- Refuse cross-mode leakage

## Response snapshot

Generated comprehensive `tasks.md` with **70 tasks** across **9 phases**:

**Phase 1: Security Foundation (BLOCKING)** - 11 tasks
- `.env.example` creation
- `.gitignore` updates
- Pydantic Settings implementation
- Lifespan validation
- 5 startup failure tests (one per credential)

**Phase 2: US3 - Secure Backend Startup** - 4 tasks
- Enhanced error messages
- Health endpoint credential check
- Error message sanitization

**Phase 3: US1 - Book Mode RAG Query (MVP)** - 12 tasks
- Cohere embedding service
- Qdrant vector store
- RAG query service
- API endpoints
- Citation extraction
- Tests

**Phase 4: US2 - Selection-Only Mode** - 8 tasks
- Selected text parameter
- Mode isolation (CRITICAL)
- Validation
- 3 mode isolation tests

**Phase 5: US4 - Frontend Secret Isolation** - 11 tasks
- RAGChatWidget component
- Text selection hook
- Backend proxy calls
- Secret verification checks

**Phase 6: US5 - Credential Setup Guidance** - 5 tasks
- Documentation
- Setup guide

**Phase 7: US6 - Module Filtering** - 5 tasks
- Module filter parameter
- Qdrant filter query
- Frontend selector

**Phase 8: Guardrails & Validation** - 7 tasks
- Input validation
- Error sanitization
- Security tests

**Phase 9: Deployment Preparation** - 6 tasks
- Dockerfile
- CORS configuration
- Health checks

**Key Security Constraints Enforced**:
- Phase 1 BLOCKS all other phases
- Selection mode NEVER queries Qdrant (Constitution P4)
- Frontend has ZERO secrets (Constitution P5)
- Backend fails fast on missing credentials (Constitution S2)

## Outcome

- ✅ Impact: Complete task breakdown aligned with Constitution v2.0.0 security requirements
- 🧪 Tests: 13 test tasks defined (security, mode isolation, RAG functionality)
- 📁 Files: 1 file created (tasks.md with 70 tasks)
- 🔁 Next prompts: /sp.implement to begin execution
- 🧠 Reflection: Security-first phase ordering ensures no credential leakage

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): PASS - All tasks traceable to user stories, security constraints preserved
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Run /sp.implement starting with Phase 1 Security Foundation
