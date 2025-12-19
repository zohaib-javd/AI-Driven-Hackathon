# Physical AI RAG Backend

Secure, production-ready RAG (Retrieval-Augmented Generation) backend for the Physical AI & Humanoid Robotics book.

## Security Features

- **Zero Hardcoded Secrets** - All credentials loaded from environment variables
- **Fail-Fast Validation** - Backend refuses to start if any credential is missing
- **Sanitized Errors** - Internal error details never exposed to clients
- **Mode Isolation** - Selection-only mode strictly isolated from vector database
- **Frontend Isolation** - Frontend has zero access to API keys

## Quick Start

### 1. Clone and Setup

```bash
cd backend
cp .env.example .env
```

### 2. Get Your Credentials

You need the following credentials before the backend will start:

| Variable | Description | Where to Get It |
|----------|-------------|-----------------|
| `COHERE_API_KEY` | Cohere API key for embeddings | [dashboard.cohere.com/api-keys](https://dashboard.cohere.com/api-keys) |
| `OPENAI_API_KEY` | OpenAI API key for chat | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `QDRANT_URL` | Qdrant Cloud URL | [cloud.qdrant.io](https://cloud.qdrant.io) |
| `QDRANT_API_KEY` | Qdrant API key | [cloud.qdrant.io](https://cloud.qdrant.io) |
| `DATABASE_URL` | Neon Postgres connection string | [console.neon.tech](https://console.neon.tech) |

### 3. Configure Your `.env` File

Edit the `.env` file and add your credentials:

```env
COHERE_API_KEY=your-cohere-api-key
OPENAI_API_KEY=sk-your-openai-api-key
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key
DATABASE_URL=postgresql+asyncpg://user:pass@host/db?sslmode=require
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the Backend

```bash
uvicorn src.main:app --reload
```

The backend will:
1. Validate all credentials on startup
2. Exit immediately with a clear error if any are missing
3. Start accepting requests only after all credentials are validated

## API Endpoints

### Book Mode (Full RAG)

```bash
POST /api/rag/query
{
  "query": "What is ROS 2?",
  "top_k": 5,
  "module_filter": "module-1-ros2",
  "temperature": 0.7
}
```

### Selection-Only Mode (No Qdrant)

```bash
POST /api/rag/query-selection
{
  "query": "Explain this code",
  "selected_text": "def create_node()...",
  "temperature": 0.7
}
```

**CRITICAL**: Selection-only mode NEVER queries Qdrant. It uses ONLY the provided text.

### Health Check

```bash
GET /health
```

Returns credential validation status without exposing values.

### Stats

```bash
GET /api/rag/stats
```

Returns system configuration (no secrets exposed).

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Embeddings | Cohere | embed-english-v3.0 (1024 dim) |
| Vector DB | Qdrant Cloud | Latest |
| Metadata DB | Neon Postgres | Serverless |
| Chat | OpenAI | gpt-4-turbo-preview |
| Framework | FastAPI | Latest |
| Python | Python | 3.11+ |

## Docker Deployment

```bash
# Build
docker build -t physical-ai-backend .

# Run with credentials
docker run -p 8000:8000 \
  -e COHERE_API_KEY=your-key \
  -e OPENAI_API_KEY=your-key \
  -e QDRANT_URL=your-url \
  -e QDRANT_API_KEY=your-key \
  -e DATABASE_URL=your-url \
  physical-ai-backend
```

## Security Validation

The backend enforces these security requirements:

1. **Startup Validation**: All 5 required credentials must be present
2. **Error Sanitization**: Internal errors never exposed to clients
3. **Mode Isolation**: Selection mode NEVER touches Qdrant
4. **No Credential Logging**: Credentials never appear in logs
5. **Health Check**: Reports credential status without exposing values

## Error Messages

If credentials are missing, you'll see:

```
CRITICAL - Missing required credential(s): COHERE_API_KEY, OPENAI_API_KEY
CRITICAL - The backend cannot start without all required credentials.
CRITICAL - Please check your .env file and ensure all credentials are set.
```

## License

MIT
