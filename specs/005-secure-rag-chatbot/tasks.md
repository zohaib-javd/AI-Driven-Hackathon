# Tasks: Secure Dynamic RAG Chatbot

**Input**: Design documents from `/specs/005-secure-rag-chatbot/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)
**Constitution Version**: 2.0.0
**Branch**: `005-secure-rag-chatbot`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US6)
- Include exact file paths in descriptions

## Path Conventions (Web App)

- **Backend**: `backend/src/`
- **Frontend**: `physical-ai-humanoid-robotics/src/`
- **Tests**: `backend/tests/`

---

## Phase 1: Security Foundation (BLOCKING - NON-OPTIONAL)

**Purpose**: Establish secure credential handling BEFORE any external API integration.

**CRITICAL**: No API calls, no external services until this phase is 100% complete.

### Security Setup

- [ ] T001 [US3] Create `.env.example` with all required credentials documented (empty values) in `backend/.env.example`
- [ ] T002 [P] [US3] Update `.gitignore` to exclude all secret files (`.env`, `*.env`, `.env.local`) in repository root
- [ ] T003 [US3] Implement Pydantic Settings class with fail-fast validation in `backend/src/config.py`
- [ ] T004 [US3] Add lifespan event to validate all credentials on startup in `backend/src/main.py`
- [ ] T005 [US3] Create startup validation test - backend MUST refuse to start with missing `COHERE_API_KEY` in `backend/tests/test_security.py`
- [ ] T006 [P] [US3] Create startup validation test - backend MUST refuse to start with missing `OPENAI_API_KEY` in `backend/tests/test_security.py`
- [ ] T007 [P] [US3] Create startup validation test - backend MUST refuse to start with missing `QDRANT_URL` in `backend/tests/test_security.py`
- [ ] T008 [P] [US3] Create startup validation test - backend MUST refuse to start with missing `QDRANT_API_KEY` in `backend/tests/test_security.py`
- [ ] T009 [P] [US3] Create startup validation test - backend MUST refuse to start with missing `NEON_DATABASE_URL` in `backend/tests/test_security.py`

### Credential Request Protocol

- [ ] T010 [US5] Create setup documentation listing all required credentials with descriptions in `backend/README.md`
- [ ] T011 [US5] Document credential acquisition steps (Cohere, OpenAI, Qdrant, Neon) in `backend/README.md`

**Checkpoint**: Backend refuses to start without ALL required credentials. Zero secrets in code.

---

## Phase 2: User Story 3 - Secure Backend Startup (Priority: P1)

**Goal**: Backend validates all required credentials on startup and refuses to operate if any are missing.

**Independent Test**: Remove one environment variable and verify backend exits with clear error message.

### Implementation

- [ ] T012 [US3] Enhance config.py with clear error messages identifying missing credential in `backend/src/config.py`
- [ ] T013 [US3] Add credential presence check (not value check) in health endpoint in `backend/src/api/health.py`
- [ ] T014 [US3] Ensure error messages do NOT expose other secret values in `backend/src/config.py`
- [ ] T015 [US3] Manual test: Verify backend fails fast with "Missing required credential: COHERE_API_KEY"

**Checkpoint**: US3 complete - Backend refuses to start with missing credentials

---

## Phase 3: User Story 1 - Book Mode RAG Query (Priority: P1) MVP

**Goal**: Reader asks a question, chatbot retrieves relevant content from vector database and provides grounded answer with citations.

**Independent Test**: Ask "What is a ROS 2 topic?" and verify response includes Module 1 content with citations.

### Backend Services

- [ ] T016 [US1] Implement Cohere embedding service (embed-english-v3.0, 1024 dim) in `backend/src/services/embeddings.py`
- [ ] T017 [US1] Implement Qdrant vector store client with search method in `backend/src/services/vectorstore.py`
- [ ] T018 [US1] Implement RAG query service with Book mode in `backend/src/services/rag.py`
- [ ] T019 [US1] Define ChatMode enum (book, selection) in `backend/src/services/rag.py`
- [ ] T020 [US1] Implement citation extraction from search results in `backend/src/services/rag.py`
- [ ] T021 [US1] Implement context formatting with [Module, Chapter] format in `backend/src/services/rag.py`
- [ ] T022 [US1] Implement OpenAI response generation with grounding prompt in `backend/src/services/rag.py`

### API Endpoints

- [ ] T023 [US1] Create QueryRequest Pydantic model with mode, query, session_id in `backend/src/api/rag.py`
- [ ] T024 [US1] Create QueryResponse Pydantic model with answer, citations, mode in `backend/src/api/rag.py`
- [ ] T025 [US1] Implement POST `/api/rag/query` endpoint for Book mode in `backend/src/api/rag.py`
- [ ] T026 [US1] Add grounding validation - respond "I couldn't find relevant information" for zero results in `backend/src/services/rag.py`

### Tests

- [ ] T027 [P] [US1] Test Book mode queries Qdrant (assert `vectorstore.search` called) in `backend/tests/test_rag.py`
- [ ] T028 [P] [US1] Test citations include module, chapter, section in `backend/tests/test_rag.py`

**Checkpoint**: US1 complete - Book Mode RAG query returns grounded answers with citations

---

## Phase 4: User Story 2 - Selection-Only Mode (Priority: P1)

**Goal**: Reader highlights text and gets answers using ONLY that text, with NO vector database queries.

**Independent Test**: Highlight "ROS 2 uses DDS", ask about it, verify NO Qdrant calls.

**CRITICAL SECURITY**: Selection mode MUST NEVER touch Qdrant. This is a constitution requirement.

### Backend Implementation

- [ ] T029 [US2] Add `selected_text` parameter to QueryRequest model in `backend/src/api/rag.py`
- [ ] T030 [US2] Implement Selection mode branch in RAG service - bypass Qdrant completely in `backend/src/services/rag.py`
- [ ] T031 [US2] Add validation: Selection mode requires `selected_text` (non-empty) in `backend/src/api/rag.py`
- [ ] T032 [US2] Add validation: `selected_text` max length 5000 chars in `backend/src/api/rag.py`
- [ ] T033 [US2] Return `citations: null` for Selection mode responses in `backend/src/services/rag.py`

### Mode Isolation Tests (CRITICAL)

- [ ] T034 [US2] Test Selection mode NEVER calls `vectorstore.search` (assert_not_called) in `backend/tests/test_modes.py`
- [ ] T035 [US2] Test Selection mode uses only provided text as context in `backend/tests/test_modes.py`
- [ ] T036 [US2] Test Selection mode fails without `selected_text` in `backend/tests/test_modes.py`

**Checkpoint**: US2 complete - Selection mode strictly isolated from Qdrant

---

## Phase 5: User Story 4 - Frontend Secret Isolation (Priority: P2)

**Goal**: Frontend makes API calls to backend without ANY access to API credentials.

**Independent Test**: Inspect frontend bundle - verify zero API keys or credentials.

### Frontend Implementation

- [ ] T037 [US4] Create RAGChatWidget component with mode selector in `physical-ai-humanoid-robotics/src/components/RAGChatWidget/index.tsx`
- [ ] T038 [US4] Implement text selection hook (useTextSelection) in `physical-ai-humanoid-robotics/src/components/RAGChatWidget/index.tsx`
- [ ] T039 [US4] Implement API call to `/api/rag/query` (backend proxy only) in `physical-ai-humanoid-robotics/src/components/RAGChatWidget/index.tsx`
- [ ] T040 [US4] Add loading indicator during requests in `physical-ai-humanoid-robotics/src/components/RAGChatWidget/index.tsx`
- [ ] T041 [US4] Add user-friendly error handling (no raw error details) in `physical-ai-humanoid-robotics/src/components/RAGChatWidget/index.tsx`
- [ ] T042 [P] [US4] Create chat widget styles in `physical-ai-humanoid-robotics/src/components/RAGChatWidget/styles.module.css`
- [ ] T043 [US4] Add widget to Root theme wrapper in `physical-ai-humanoid-robotics/src/theme/Root.tsx`

### Frontend Isolation Verification

- [ ] T044 [US4] Verify NO direct calls to Cohere API in frontend code
- [ ] T045 [P] [US4] Verify NO direct calls to OpenAI API in frontend code
- [ ] T046 [P] [US4] Verify NO direct calls to Qdrant API in frontend code
- [ ] T047 [US4] Verify NO API keys or tokens in any frontend file

**Checkpoint**: US4 complete - Frontend has zero secrets, all calls through backend

---

## Phase 6: User Story 5 - Credential Setup Guidance (Priority: P2)

**Goal**: Developer can configure and run the system within 15 minutes using documentation.

**Independent Test**: Fresh clone, follow setup docs, all services connect successfully.

### Documentation

- [ ] T048 [US5] Create `backend/.env.example` with all variables documented in `backend/.env.example`
- [ ] T049 [US5] Document required credentials table in backend README in `backend/README.md`
- [ ] T050 [US5] Add step-by-step credential acquisition guide in `backend/README.md`
- [ ] T051 [US5] Document backend startup command in `backend/README.md`
- [ ] T052 [US5] Document frontend proxy configuration in `physical-ai-humanoid-robotics/README.md`

**Checkpoint**: US5 complete - New developer can set up system in 15 minutes

---

## Phase 7: User Story 6 - Module Filtering (Priority: P3)

**Goal**: Reader can filter chatbot responses to specific book modules.

**Independent Test**: Select "Module 3" filter, ask question, verify results from Module 3 only.

### Backend Implementation

- [ ] T053 [US6] Add `module_filter` parameter to QueryRequest model in `backend/src/api/rag.py`
- [ ] T054 [US6] Implement module filter in Qdrant search query in `backend/src/services/vectorstore.py`
- [ ] T055 [US6] Test module filter returns only matching module results in `backend/tests/test_rag.py`

### Frontend Implementation

- [ ] T056 [US6] Add module selector dropdown to chat widget in `physical-ai-humanoid-robotics/src/components/RAGChatWidget/index.tsx`
- [ ] T057 [US6] Pass selected module filter in API request in `physical-ai-humanoid-robotics/src/components/RAGChatWidget/index.tsx`

**Checkpoint**: US6 complete - Module filtering works in Book mode

---

## Phase 8: Guardrails & Validation

**Purpose**: Enforce security boundaries and input validation across all user stories.

### Input Validation

- [ ] T058 [US1] Add query length validation (max 2000 chars) in `backend/src/api/rag.py`
- [ ] T059 [US2] Add selected_text length validation (min 10, max 5000 chars) in `backend/src/api/rag.py`
- [ ] T060 Implement error sanitization - never expose internal error details in `backend/src/api/rag.py`
- [ ] T061 Add structured logging (never log credential values) in `backend/src/main.py`

### Security Tests

- [ ] T062 [P] Test error messages do not contain secret values in `backend/tests/test_security.py`
- [ ] T063 [P] Test error messages do not contain stack traces in `backend/tests/test_security.py`
- [ ] T064 Scan frontend bundle for secrets (automated check) in `backend/tests/test_security.py`

**Checkpoint**: All guardrails in place, security tests passing

---

## Phase 9: Deployment Preparation

**Purpose**: Secure deployment with environment variable injection.

### Docker Configuration

- [ ] T065 Create Dockerfile (no secrets in image) in `backend/Dockerfile`
- [ ] T066 Configure CORS for frontend domain only in `backend/src/main.py`
- [ ] T067 Implement comprehensive health check endpoint in `backend/src/api/health.py`

### Deployment Verification

- [ ] T068 Verify Docker image builds without secrets
- [ ] T069 Verify container starts with environment variables
- [ ] T070 Run quickstart.md validation (fresh clone test)

**Checkpoint**: Deployment ready with secure configuration

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Security Foundation) ─── BLOCKS EVERYTHING ───┐
                                                        │
Phase 2 (US3 - Secure Startup) ◄────────────────────────┤
                                                        │
Phase 3 (US1 - Book Mode) ◄─────────────────────────────┤
         │                                              │
         ▼                                              │
Phase 4 (US2 - Selection Mode) ◄───────────────────────┤
         │                                              │
         ▼                                              │
Phase 5 (US4 - Frontend Isolation) ◄───────────────────┤
         │                                              │
         ├──► Phase 6 (US5 - Documentation)            │
         │                                              │
         └──► Phase 7 (US6 - Module Filter) [Optional] │
                                                        │
Phase 8 (Guardrails) ◄─────────────────────────────────┘
         │
         ▼
Phase 9 (Deployment)
```

### Critical Path (MVP)

1. **Phase 1**: Security Foundation (MANDATORY FIRST)
2. **Phase 2**: US3 - Secure Backend Startup
3. **Phase 3**: US1 - Book Mode RAG Query
4. **Phase 4**: US2 - Selection-Only Mode
5. **Phase 5**: US4 - Frontend Secret Isolation
6. **Phase 8**: Guardrails (subset for MVP)

### Parallel Opportunities

- T001, T002: Can run in parallel (different files)
- T005-T009: All startup tests can run in parallel
- T016, T017: Embedding and vectorstore can run in parallel
- T027, T028: RAG tests can run in parallel
- T034-T036: Mode isolation tests can run in parallel
- T042, T043: CSS and Root.tsx can run in parallel
- T044-T047: Frontend verification can run in parallel
- T062-T064: Security tests can run in parallel

---

## Implementation Strategy

### Security-First Approach

1. **STOP** - Before ANY external API call, Phase 1 MUST be complete
2. All credentials MUST be in `.env` (never in code)
3. Backend MUST fail to start if credentials missing
4. Frontend MUST have zero secrets

### MVP Delivery (Book + Selection Mode)

1. Complete Phase 1 (Security) - BLOCKING
2. Complete Phase 2 (US3) - Backend startup validation
3. Complete Phase 3 (US1) - Book Mode working
4. Complete Phase 4 (US2) - Selection Mode working
5. Complete Phase 5 (US4) - Frontend connected
6. **STOP and VALIDATE**: Test both modes independently
7. Deploy MVP

### User Story Traceability

| Task Range | User Story | Priority | Description |
|------------|------------|----------|-------------|
| T001-T015 | US3 | P1 | Secure Backend Startup |
| T016-T028 | US1 | P1 | Book Mode RAG Query |
| T029-T036 | US2 | P1 | Selection-Only Mode |
| T037-T047 | US4 | P2 | Frontend Secret Isolation |
| T048-T052 | US5 | P2 | Credential Setup Guidance |
| T053-T057 | US6 | P3 | Module Filtering |
| T058-T064 | All | - | Guardrails |
| T065-T070 | All | - | Deployment |

---

## Notes

- **Security is NON-NEGOTIABLE**: Phase 1 must complete before any external API integration
- **Mode Isolation is CRITICAL**: Selection mode must NEVER query Qdrant (Constitution requirement)
- **Frontend has ZERO secrets**: All external API calls proxied through backend
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
