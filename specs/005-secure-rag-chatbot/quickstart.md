# Quickstart Guide: Secure Dynamic RAG Chatbot

**Feature Branch**: `005-secure-rag-chatbot`
**Time to Complete**: ~15 minutes

## Prerequisites

- Python 3.11+
- Node.js 18+
- Git

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repo-url>
cd Hackathon01

# Checkout the feature branch
git checkout 005-secure-rag-chatbot
```

## Step 2: Obtain Required Credentials

You need API keys from the following services:

| Service | Purpose | Get It Here |
|---------|---------|-------------|
| **Cohere** | Text embeddings | https://dashboard.cohere.com/api-keys |
| **OpenAI** | Chat completion | https://platform.openai.com/api-keys |
| **Qdrant Cloud** | Vector storage | https://cloud.qdrant.io/ |
| **Neon** | Postgres database | https://console.neon.tech/ |

## Step 3: Configure Environment Variables

```bash
# Navigate to backend directory
cd backend

# Copy the example environment file
cp .env.example .env

# Edit .env with your actual credentials
```

Edit `.env` with your credentials:

```env
# Required - Cohere Embeddings
COHERE_API_KEY=your-cohere-api-key-here

# Required - OpenAI Chat
OPENAI_API_KEY=sk-your-openai-api-key-here

# Required - Qdrant Vector Database
QDRANT_URL=https://your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key-here

# Required - Neon Postgres Database
NEON_DATABASE_URL=postgresql://user:password@host/database?sslmode=require

# Optional - Configuration
COLLECTION_NAME=book_chunks
EMBEDDING_MODEL=embed-english-v3.0
CHAT_MODEL=gpt-4-turbo-preview
```

## Step 4: Install Backend Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 5: Verify Backend Startup

```bash
# Start the backend server
uvicorn src.main:app --reload

# Expected output:
# INFO:     Started server process [12345]
# INFO:     Waiting for application startup.
# INFO:     All credentials validated successfully
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://127.0.0.1:8000
```

**If startup fails**, you'll see an error like:
```
ERROR: Missing required credential: COHERE_API_KEY
```

This means the credential is missing or invalid. Check your `.env` file.

## Step 6: Install Frontend Dependencies

```bash
# Open a new terminal
cd physical-ai-humanoid-robotics

# Install dependencies
npm install
```

## Step 7: Start Frontend

```bash
# Start development server
npm start

# Opens browser at http://localhost:3000
```

## Step 8: Test the Chatbot

1. Navigate to any book page
2. Look for the chat widget in the bottom-right corner
3. Try **Book Mode**: Ask "What is a ROS 2 topic?"
4. Try **Selection Mode**: Highlight some text, then ask about it

## Verify Security

### Check 1: Backend Fails Without Credentials
```bash
# Remove one credential
unset COHERE_API_KEY

# Try to start backend
uvicorn src.main:app --reload
# Should fail with: "Missing required credential: COHERE_API_KEY"
```

### Check 2: Frontend Has No Secrets
```bash
# Build frontend
npm run build

# Search for secrets in build output
grep -r "sk-" ./build/  # Should return nothing
grep -r "COHERE" ./build/  # Should return nothing
```

### Check 3: Network Traffic
1. Open browser DevTools → Network tab
2. Use the chatbot
3. Verify all requests go to `/api/rag/*`
4. Verify NO direct requests to `api.cohere.ai`, `api.openai.com`, or `qdrant.io`

## Common Issues

### "Missing required credential" on startup
- Ensure `.env` file exists in `backend/` directory
- Ensure all variables are set (no empty values)
- Restart the backend after editing `.env`

### "Connection refused" in frontend
- Ensure backend is running on port 8000
- Check CORS settings in backend

### "Selection mode not working"
- Ensure you've highlighted text before sending
- Minimum 10 characters required
- Maximum 5000 characters allowed

## Next Steps

1. **Ingest Book Content**: Run the ingestion pipeline to populate Qdrant
2. **Deploy**: See deployment guide for production setup
3. **Monitor**: Check health endpoint at `/api/rag/health`

## Health Check

```bash
curl http://localhost:8000/api/rag/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "qdrant": true,
    "openai": true,
    "cohere": true,
    "database": true
  },
  "timestamp": "2025-12-18T10:30:00Z"
}
```
