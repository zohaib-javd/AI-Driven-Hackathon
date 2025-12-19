<!--
SYNC IMPACT REPORT
==================
Version Change: 1.0.1 → 2.0.0 (MAJOR)
Bump Rationale: Major governance redefinition with security-first architecture, new AI behavior rules,
and strict secret handling requirements. This fundamentally changes project principles.

Modified Principles:
- "Framework Standards" → "Security Architecture Standards" (redefined)
- "Code Quality Standards" → "Secret Management Standards" (redefined)
- "Educational Principles" → "AI Behavior Rules" (redefined)
- "Documentation Reference Standards" → "Selection-Only Mode Enforcement" (redefined)

Added Sections:
- Core Principles (5 new security-focused principles)
- AI Behavior Rules (4 mandatory rules)
- Security Standards (5 standards)
- Technology Constraints (mandatory stack)
- Trust Boundaries (frontend/backend separation)

Removed Sections:
- Educational Principles (moved to supplementary)
- Pedagogical Standards (moved to supplementary)
- Risk Management (consolidated into Security Standards)

Templates Verified:
✅ .specify/templates/plan-template.md - Constitution Check section compatible with security gates
✅ .specify/templates/spec-template.md - Requirements section supports security criteria
✅ .specify/templates/tasks-template.md - Task structure supports security validation phases

Follow-up TODOs: None
-->

# Physical AI & Humanoid Robotics — Secure RAG Chatbot + Book Platform

## Constitution

**Version**: 2.0.0 | **Ratified**: 2025-12-15 | **Last Amended**: 2025-12-18

## Mission Statement

To create a comprehensive, technically accurate book on Physical AI and Humanoid Robotics with an integrated RAG chatbot that maintains **production-grade security posture**, **zero secret leakage**, and **deterministic AI behavior** throughout all operations.

## Core Principles

### Principle 1: Security-First Architecture

All system design decisions MUST prioritize security over convenience. The architecture MUST enforce clear separation between trusted (backend) and untrusted (frontend) components. Security controls MUST be implemented at every layer.

**Rationale**: A RAG chatbot handling book content requires robust security to prevent unauthorized access, secret exposure, and ensure AI responses remain grounded and safe.

### Principle 2: Zero Hardcoded Secrets

No credentials, API keys, tokens, or sensitive configuration values MUST ever appear in source code, prompts, or client-side code. All secrets MUST be injected exclusively via environment variables at runtime.

**Rationale**: Hardcoded secrets are the leading cause of security breaches. Environment variable injection ensures secrets never enter version control or client bundles.

### Principle 3: Grounded AI Responses Only

All AI-generated responses MUST be grounded in retrieved content from the book or user-selected text. The system MUST NOT hallucinate, fabricate citations, or generate responses without supporting context.

**Rationale**: A RAG chatbot must provide accurate, verifiable answers. Ungrounded responses undermine trust and educational value.

### Principle 4: Deterministic Retrieval Behavior

The retrieval system MUST behave predictably and consistently. Selection-only mode MUST strictly use only user-selected text without any Qdrant queries. Book mode MUST query Qdrant for context.

**Rationale**: Predictable retrieval behavior enables testing, debugging, and user trust. Mode confusion could lead to information leakage or incorrect responses.

### Principle 5: Clear Trust Boundaries

Frontend code MUST be treated as untrusted. Backend MUST validate all inputs. Secrets MUST never cross trust boundaries. The frontend MUST NOT have access to any API keys or credentials.

**Rationale**: Frontend code runs in user browsers and can be inspected or modified. Only the backend can be trusted with secrets and critical operations.

## AI Behavior Rules

These rules govern how AI components (LLMs, agents) MUST behave within this system:

### Rule 1: NEVER Assume Credentials Exist

AI agents MUST NOT assume that API keys, database connections, or other credentials are available. If a credential is required for an operation, the agent MUST explicitly check for its presence and fail gracefully if missing.

### Rule 2: ALWAYS Request Credentials Explicitly

When credentials are needed, AI agents MUST request them through proper channels (environment variables, secure configuration). Agents MUST NOT attempt to generate, guess, or derive credentials.

### Rule 3: NEVER Embed Secrets Into Code or Prompts

AI agents MUST NOT include secrets in generated code, prompts sent to other services, logs, error messages, or any output that could be exposed. All secret references MUST use environment variable placeholders.

### Rule 4: ALL Credentials via Environment Variables

Every credential MUST be loaded from environment variables at runtime. Configuration files MAY reference environment variable names but MUST NOT contain actual secret values.

## Security Standards

### Standard 1: Environment Variable-Only Secret Handling

- Secrets MUST be loaded from environment variables using secure patterns
- Default values for secrets MUST be empty strings, not placeholder values
- Secret names MUST follow the pattern: `SERVICE_API_KEY`, `DATABASE_URL`
- The `.env.example` file MUST document required variables without values

### Standard 2: Fail-Fast on Missing Secrets

- Application MUST validate all required secrets on startup
- Missing required secrets MUST cause immediate startup failure with clear error messages
- Error messages MUST identify which secret is missing without exposing other secrets
- Graceful degradation MUST NOT be used for critical security credentials

### Standard 3: Frontend Secret Isolation

- Frontend code MUST NOT contain, reference, or access any secrets
- API calls from frontend MUST go through backend proxy endpoints
- Frontend MUST NOT have direct access to Cohere, OpenAI, Qdrant, or Neon
- Backend MUST be the sole holder of all external service credentials

### Standard 4: Backend Secret Validation

- Backend MUST validate presence of all secrets before accepting requests
- Health check endpoints MUST verify secret availability (not values)
- Secrets MUST be loaded once at startup and cached in memory
- Secret refresh MUST require application restart (no hot-reload)

### Standard 5: Selection-Only Mode Isolation

- When in selection-only mode, the system MUST NOT query Qdrant
- Selected text MUST be passed directly to LLM without vector retrieval
- Mode selection MUST be explicit in API requests
- Backend MUST enforce mode isolation regardless of frontend behavior

## Technology Constraints

The following technology stack is MANDATORY and MUST NOT be substituted without constitutional amendment:

| Component | Technology | Version/Model |
|-----------|------------|---------------|
| Embeddings | Cohere | embed-english-v3.0 (1024 dim) |
| Vector DB | Qdrant Cloud | Latest stable |
| Metadata DB | Neon Serverless Postgres | Latest stable |
| Reasoning/Chat | OpenAI | gpt-4-turbo-preview |
| Frontend | Docusaurus (React) | v3.x |
| Backend | FastAPI (Python) | Python 3.11+ |

**Rationale**: Fixed technology stack ensures consistent security analysis, known vulnerability surfaces, and predictable behavior across deployments.

## Success Criteria

### Security Success

- [ ] Zero secret leakage in source code, logs, or client bundles
- [ ] All secrets injected via environment variables only
- [ ] Frontend has zero access to any API credentials
- [ ] Backend validates all secrets on startup (fail-fast)
- [ ] Selection-only mode strictly isolated from Qdrant

### Functional Success

- [ ] RAG chatbot provides grounded responses with citations
- [ ] Book mode correctly queries Qdrant for context
- [ ] Selection-only mode uses only provided text
- [ ] All 4 book modules accessible and searchable
- [ ] Voice input processed securely (if enabled)

### Operational Success

- [ ] Production deployment follows security standards
- [ ] Monitoring detects secret access anomalies
- [ ] Incident response procedures documented
- [ ] Regular security audits scheduled

## Governance

### Amendment Procedure

1. Proposed changes MUST be documented with security impact analysis
2. Security-related changes MUST undergo security review
3. Major changes (principles, security standards) require explicit approval
4. Version MUST be incremented according to semantic versioning:
   - **MAJOR**: Principle changes, security standard modifications, trust boundary changes
   - **MINOR**: New guidance, additional standards, expanded coverage
   - **PATCH**: Clarifications, typo fixes, non-security refinements

### Compliance Review

- All code changes MUST be reviewed against security standards
- Secrets MUST be audited before each deployment
- Selection-only mode MUST be tested with each release
- Non-compliance MUST block deployment until resolved

### Versioning Policy

- Constitution version MUST be tracked in this document
- All dependent artifacts MUST reference constitution version
- Breaking changes MUST increment MAJOR version
- Changelog MUST document all amendments

---

## Supplementary: Educational Standards

*These standards supplement the core security principles for book content quality:*

- All code examples MUST be validated in target environments
- Learning objectives MUST be stated at chapter beginnings
- "Learn → Simulate → Deploy" pedagogy MUST be followed
- Technical claims MUST reference official documentation

## Supplementary: Book Module Structure

- **Module 1**: ROS 2 Fundamentals and Robotic Systems
- **Module 2**: Simulation Environments and Digital Twins
- **Module 3**: NVIDIA Isaac and Advanced Perception
- **Module 4**: Vision-Language-Action Models and Embodied AI

---

*This constitution establishes the security-first foundation for the Physical AI & Humanoid Robotics platform. All development, deployment, and operational decisions MUST align with these principles.*
