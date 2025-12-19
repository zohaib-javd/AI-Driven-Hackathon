# Feature Specification: Secure Dynamic RAG Chatbot

**Feature Branch**: `005-secure-rag-chatbot`
**Created**: 2025-12-18
**Status**: Draft
**Constitution Version**: 2.0.0

## Overview

A secure, dynamic RAG (Retrieval-Augmented Generation) chatbot for the Physical AI & Humanoid Robotics book platform. The chatbot provides context-aware answers from book content while enforcing strict security boundaries for credential handling and supporting a text-selection-only answering mode.

**Target Audience**:
- Readers of the Physical AI & Humanoid Robotics book
- Robotics and AI practitioners

**Out of Scope**:
- Model training or fine-tuning
- Frontend authentication/login systems
- Secret management UI or dashboard

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Book Mode RAG Query (Priority: P1)

A reader opens the chatbot and asks a question about ROS 2 topics. The chatbot retrieves relevant content from the book's vector database and provides a grounded answer with citations.

**Why this priority**: This is the core value proposition - readers need accurate, book-grounded answers to learn effectively. Without this, the chatbot has no purpose.

**Independent Test**: Can be fully tested by asking "What is a ROS 2 topic?" and verifying the response includes content from Module 1 with proper citations.

**Acceptance Scenarios**:

1. **Given** the chatbot is open and backend is running with valid credentials, **When** user types "What is URDF?", **Then** chatbot returns an answer containing content from the book with at least one citation reference.

2. **Given** the chatbot is open, **When** user asks about a topic covered in Module 3 (Isaac), **Then** chatbot retrieves relevant chunks from Module 3 and provides a grounded response.

3. **Given** the chatbot is open, **When** user asks about something not in the book, **Then** chatbot responds with "I couldn't find relevant information in the book" rather than hallucinating.

---

### User Story 2 - Selection-Only Mode (Priority: P1)

A reader highlights a code snippet or paragraph on the book page and clicks "Ask about this selection." The chatbot answers ONLY using the highlighted text, without querying the vector database.

**Why this priority**: Critical feature per constitution - selection-only mode MUST be strictly isolated from vector retrieval to ensure deterministic behavior and prevent information leakage.

**Independent Test**: Can be tested by highlighting text, asking a question, and verifying the response uses ONLY the selected text content.

**Acceptance Scenarios**:

1. **Given** user has highlighted text "ROS 2 uses DDS for communication", **When** user clicks "Ask about selection" and types "What does this text say about communication?", **Then** chatbot answers using ONLY the highlighted text without querying vector database.

2. **Given** user has highlighted a code snippet, **When** user asks "Explain this code", **Then** chatbot explains the code using only the visible snippet content.

3. **Given** selection-only mode is active, **When** backend receives the request, **Then** backend MUST NOT make any calls to the vector database (Qdrant).

---

### User Story 3 - Secure Backend Startup (Priority: P1)

When the backend service starts, it validates that all required credentials (Cohere API key, OpenAI API key, Qdrant credentials, Neon database URL) are present in environment variables. If any are missing, the service refuses to start.

**Why this priority**: Security-critical per constitution - fail-fast on missing secrets prevents the system from operating in an insecure state.

**Independent Test**: Can be tested by removing one environment variable and verifying the backend exits with a clear error message.

**Acceptance Scenarios**:

1. **Given** all required environment variables are set, **When** backend starts, **Then** it initializes successfully and begins accepting requests.

2. **Given** COHERE_API_KEY is missing from environment, **When** backend attempts to start, **Then** it exits immediately with error "Missing required credential: COHERE_API_KEY".

3. **Given** OPENAI_API_KEY is missing from environment, **When** backend attempts to start, **Then** it exits immediately with error "Missing required credential: OPENAI_API_KEY".

4. **Given** any required credential is missing, **When** backend attempts to start, **Then** it MUST NOT accept any HTTP requests.

---

### User Story 4 - Frontend Secret Isolation (Priority: P2)

The frontend chatbot component makes API calls to the backend without ever handling, storing, or having access to any API credentials. All external service calls (Cohere, OpenAI, Qdrant) are made server-side only.

**Why this priority**: Security requirement - frontend code is untrusted and MUST NOT contain secrets. Lower priority because it's an architectural constraint enforced during development.

**Independent Test**: Can be tested by inspecting the frontend bundle and verifying zero API keys or credentials are present.

**Acceptance Scenarios**:

1. **Given** frontend is built for production, **When** bundle is inspected, **Then** no API keys, tokens, or credentials are found in any JavaScript/TypeScript files.

2. **Given** frontend sends a chat request, **When** request is made, **Then** it goes to backend endpoint `/api/rag/query` without any authentication headers containing API keys.

3. **Given** user opens browser developer tools, **When** they inspect network requests from the chatbot, **Then** no requests are made directly to Cohere, OpenAI, or Qdrant APIs.

---

### User Story 5 - Credential Setup Guidance (Priority: P2)

When a developer sets up the project, they receive clear instructions on which credentials are needed and how to configure them via `.env` file. A `.env.example` file documents all required variables.

**Why this priority**: Developer experience - clear setup instructions reduce configuration errors and prevent accidental secret exposure.

**Independent Test**: Can be tested by following the setup instructions with a fresh clone and verifying all services connect successfully.

**Acceptance Scenarios**:

1. **Given** a fresh project clone, **When** developer reads setup documentation, **Then** they find a list of all required credentials with descriptions.

2. **Given** `.env.example` exists, **When** developer copies it to `.env`, **Then** they see placeholder entries for all required credentials without actual values.

3. **Given** developer has obtained all API keys, **When** they populate `.env` and start the backend, **Then** all services connect successfully.

---

### User Story 6 - Module Filtering (Priority: P3)

A reader can filter chatbot responses to specific book modules (e.g., "Only search Module 1: ROS 2"). This helps focus answers on the current topic they're studying.

**Why this priority**: Enhanced user experience - useful but not essential for core functionality.

**Independent Test**: Can be tested by selecting "Module 3" filter and asking a general question, verifying results come only from Module 3 content.

**Acceptance Scenarios**:

1. **Given** user selects "Module 1: ROS 2" filter, **When** they ask "What is a topic?", **Then** results come exclusively from Module 1 content.

2. **Given** no filter is selected (default), **When** user asks a question, **Then** results may come from any module.

---

### Edge Cases

- What happens when the vector database returns zero results? → Chatbot responds with "I couldn't find relevant information" without hallucinating.
- What happens when selected text is empty or too short? → Chatbot prompts user to "Please select some text first."
- What happens when backend loses connection to Qdrant mid-request? → Request fails gracefully with user-friendly error message.
- What happens when API rate limits are exceeded? → Backend returns appropriate error and chatbot displays "Service temporarily busy, please try again."
- What happens if `.env` file has malformed values? → Backend validation catches invalid format and fails fast with specific error.

## Requirements *(mandatory)*

### Functional Requirements

**RAG Core**:
- **FR-001**: System MUST retrieve relevant content from the book's vector database when answering questions in Book Mode.
- **FR-002**: System MUST provide citations (module, chapter, section) with each answer in Book Mode.
- **FR-003**: System MUST use Cohere embeddings (embed-english-v3.0) for semantic search.
- **FR-004**: System MUST use OpenAI for generating natural language responses.

**Selection-Only Mode**:
- **FR-005**: System MUST provide a "selection-only" mode that answers using ONLY user-highlighted text.
- **FR-006**: System MUST NOT query the vector database when in selection-only mode.
- **FR-007**: System MUST clearly indicate which mode (Book or Selection) is active in the UI.

**Security - Credential Handling**:
- **FR-008**: System MUST load all credentials exclusively from environment variables.
- **FR-009**: System MUST validate presence of all required credentials on backend startup.
- **FR-010**: System MUST exit immediately with clear error message if any required credential is missing.
- **FR-011**: System MUST NOT start accepting requests until all credentials are validated.
- **FR-012**: System MUST generate and maintain a `.env.example` file documenting all required credentials.

**Security - Frontend Isolation**:
- **FR-013**: Frontend MUST NOT contain any API keys, tokens, or credentials.
- **FR-014**: Frontend MUST NOT make direct calls to external APIs (Cohere, OpenAI, Qdrant).
- **FR-015**: All external API calls MUST be proxied through the backend.

**Security - Code Quality**:
- **FR-016**: System MUST refactor any hardcoded secrets found in codebase into environment variables.
- **FR-017**: Backend MUST NOT log credential values in any log output.

**User Experience**:
- **FR-018**: Chatbot MUST display a loading indicator while processing requests.
- **FR-019**: Chatbot MUST display user-friendly error messages (not raw error details).
- **FR-020**: User MUST be able to filter results by book module.

### Key Entities

- **ChatMessage**: A single message in the conversation (role: user/assistant, content, timestamp, mode, citations if applicable)
- **Citation**: Reference to source content (module, chapter, section, relevance score, content snippet)
- **ChatSession**: A conversation session (session ID, list of messages, active mode, active filter)
- **Credential**: An API key or connection string required by the system (name, required/optional, description)

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Security Success**:
- **SC-001**: Zero API keys or credentials found in frontend bundle (verified by automated scan)
- **SC-002**: Backend refuses to start when any required credential is missing (100% of cases)
- **SC-003**: Zero hardcoded secrets in codebase (verified by secret scanning tool)

**Functional Success**:
- **SC-004**: 90% of Book Mode answers include at least one relevant citation from the book
- **SC-005**: 100% of Selection-Only Mode requests complete without any vector database queries
- **SC-006**: Users can ask a question and receive a response within 5 seconds (p95)

**User Experience Success**:
- **SC-007**: Users can complete a question-answer flow in under 30 seconds
- **SC-008**: Error messages are understandable to non-technical users (no raw stack traces)

**Developer Experience Success**:
- **SC-009**: New developer can configure and run the system within 15 minutes using documentation
- **SC-010**: `.env.example` documents 100% of required environment variables

## Assumptions

- Cohere, OpenAI, and Qdrant services are available and accessible
- Book content has already been ingested into the vector database
- Users have modern browsers with JavaScript enabled
- Backend and frontend are deployed to environments that support environment variables
- Rate limits from external APIs are sufficient for expected usage patterns
