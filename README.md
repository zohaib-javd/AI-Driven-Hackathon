# Physical AI & Humanoid Robotics - Complete Textbook System

A comprehensive 4-module textbook on Physical AI and Humanoid Robotics, built with Docusaurus and featuring an AI-powered RAG chatbot for interactive learning.

## Project Overview

This project delivers a complete educational system for learning robotics, including:

- **📚 Interactive Textbook**: 4 modules covering ROS 2, Digital Twins, NVIDIA Isaac, and VLA systems
- **🤖 AI Chatbot**: RAG-powered assistant that answers questions from the book content
- **🎤 Voice Input**: Whisper-powered speech-to-text for voice commands
- **🔬 Simulation Examples**: Hands-on code for each module
- **☁️ Cloud Deployment**: Ready for GitHub Pages, Railway, and Vercel

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interface                              │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │              Docusaurus Book (Frontend)                     │  │
│   │   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │
│   │   │ Module 1 │  │ Module 2 │  │ Module 3 │  │ Module 4 │   │  │
│   │   │  ROS 2   │  │ Gazebo   │  │  Isaac   │  │   VLA    │   │  │
│   │   └──────────┘  └──────────┘  └──────────┘  └──────────┘   │  │
│   │                                                             │  │
│   │   ┌─────────────────────────────────────────────────────┐  │  │
│   │   │  RAG ChatWidget (Text Selection + Book Query)       │  │  │
│   │   └─────────────────────────────────────────────────────┘  │  │
│   └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend                               │
│   ┌───────────────┐  ┌──────────────────────┐  ┌─────────────┐     │
│   │ /api/rag/query│  │/api/rag/query-select │  │ /api/ingest │     │
│   └───────────────┘  └──────────────────────┘  └─────────────┘     │
│                            │                                        │
│   ┌────────────────────────┼────────────────────────┐              │
│   │              RAG Pipeline with Cohere           │              │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │              │
│   │  │  Embed   │  │ Retrieve │  │ Chat (GPT-4) │  │              │
│   │  │ (Cohere) │→ │ (Qdrant) │→ │ + Citations  │  │              │
│   │  └──────────┘  └──────────┘  └──────────────┘  │              │
│   └─────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Data Storage                                  │
│   ┌───────────────────┐          ┌───────────────────┐             │
│   │   Qdrant Cloud    │          │  Neon Postgres    │             │
│   │(Cohere 1024-dim)  │          │ (Chat History)    │             │
│   └───────────────────┘          └───────────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

## RAG Chatbot Features

The chatbot uses **Cohere embed-english-v3.0** for embeddings and **OpenAI GPT-4** for chat:

- **Book Mode**: Full RAG - queries Qdrant for relevant chunks, generates answers with citations
- **Selection Mode**: Highlight text on any page, click "Ask about selection" - answers ONLY from selected text (no Qdrant query)
- **Module Filtering**: Restrict search to specific modules (ROS 2, Digital Twin, Isaac, VLA)
- **Streaming Responses**: Real-time response generation
- **Citation Cards**: Expandable source references with relevance scores

## Module Contents

### Module 1: ROS 2 - The Robotic Nervous System
- ROS 2 architecture and DDS middleware
- Nodes, topics, services, and actions
- Parameters and launch files
- URDF robot modeling
- RViz visualization
- **Mini-Project**: Joint control for humanoid robot

### Module 2: Digital Twin - Gazebo & Unity
- Gazebo physics simulation
- Importing URDF models
- Sensor simulation (LiDAR, IMU, cameras)
- Unity for robotics
- HDRP rendering
- ROS-Unity bridge
- **Mini-Project**: Full humanoid digital twin

### Module 3: AI-Robot Brain - NVIDIA Isaac
- Isaac Sim setup and configuration
- Photorealistic rendering
- Synthetic data generation
- Isaac ROS integration
- Visual SLAM (VSLAM)
- Nav2 navigation stack
- **Mini-Project**: Humanoid obstacle course navigation

### Module 4: Vision-Language-Action (VLA)
- VLA system architecture
- Whisper speech recognition
- Natural language parsing
- LLM cognitive planning
- Safety guardrails
- Manipulation control
- **Capstone**: Autonomous humanoid assistant

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker (optional, for local Qdrant)

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/your-org/physical-ai-humanoid-robotics.git
cd physical-ai-humanoid-robotics

# Install frontend dependencies
cd physical-ai-humanoid-robotics
npm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit with your API keys
# Required:
# - OPENAI_API_KEY
# - DATABASE_URL (Neon Postgres)
# - QDRANT_URL (Qdrant Cloud or localhost)
```

### 3. Start Development Servers

```bash
# Terminal 1: Start backend
cd backend
python -m uvicorn src.main:app --reload

# Terminal 2: Start frontend
cd physical-ai-humanoid-robotics
npm start
```

### 4. Ingest Book Content

```bash
# POST to ingestion endpoint
curl -X POST http://localhost:8000/api/ingest/documents \
  -H "Content-Type: application/json" \
  -d '{"docs_path": "./docs"}'
```

Visit `http://localhost:3000` to view the book and chat with the AI assistant.

## Project Structure

```
Hackathon01/
├── physical-ai-humanoid-robotics/   # Docusaurus frontend
│   ├── docs/                        # MDX book content
│   │   ├── module-1-ros2/           # ROS 2 chapters
│   │   ├── module-2-digital-twin/   # Gazebo/Unity chapters
│   │   ├── module-3-isaac/          # Isaac chapters
│   │   ├── module-4-vla/            # VLA chapters
│   │   └── glossary.mdx             # Technical glossary
│   ├── src/
│   │   └── components/
│   │       └── ChatWidget/          # AI chatbot component
│   ├── docusaurus.config.ts
│   └── sidebars.ts
│
├── backend/                         # FastAPI backend
│   ├── src/
│   │   ├── api/                     # API endpoints
│   │   │   ├── chat.py              # Chat endpoint
│   │   │   ├── ingest.py            # Document ingestion
│   │   │   └── voice.py             # Whisper voice input
│   │   ├── services/                # Business logic
│   │   │   ├── agent.py             # OpenAI agent
│   │   │   ├── embeddings.py        # Text embeddings
│   │   │   ├── retrieval.py         # RAG retrieval
│   │   │   └── vectorstore.py       # Qdrant operations
│   │   ├── models/                  # Pydantic models
│   │   └── main.py                  # FastAPI app
│   ├── tests/                       # Backend tests
│   ├── requirements.txt
│   └── Dockerfile
│
├── simulation-examples/             # Code examples
│   ├── module-1-ros2/               # ROS 2 examples
│   ├── module-2-gazebo/             # Gazebo examples
│   ├── module-3-isaac/              # Isaac examples
│   └── vla-examples/                # VLA examples
│
├── deploy/                          # Deployment configs
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── Dockerfile.frontend
│   │   └── nginx.conf
│   ├── railway.json
│   └── vercel.json
│
└── README.md
```

## Deployment

### Docker Compose (Development)

```bash
cd deploy/docker
cp .env.example .env
# Edit .env with your API keys

docker-compose --profile dev up -d
```

### Railway (Backend)

1. Connect your repository to Railway
2. Set environment variables from `.env.example`
3. Deploy the backend service

### Vercel (Frontend)

1. Import project to Vercel
2. Set `API_URL` environment variable to your Railway backend
3. Deploy

### GitHub Pages

```bash
cd physical-ai-humanoid-robotics
npm run build
npm run deploy
```

## API Endpoints

### RAG Query (Book Mode)

```http
POST /api/rag/query
Content-Type: application/json

{
  "query": "What is ROS 2?",
  "top_k": 5,
  "module_filter": "module-1-ros2",
  "min_score": 0.5,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "answer": "ROS 2 (Robot Operating System 2) is...",
  "citations": [
    {
      "chunk_id": "abc123",
      "content": "...",
      "module": "module-1-ros2",
      "section": "What is ROS 2",
      "score": 0.89
    }
  ],
  "mode": "book",
  "processing_time_ms": 1234
}
```

### RAG Query (Selection-Only Mode)

```http
POST /api/rag/query-selection
Content-Type: application/json

{
  "query": "Explain this code",
  "selected_text": "class MinimalNode(Node):\n    def __init__(self)...",
  "temperature": 0.7
}
```

**CRITICAL**: This endpoint does NOT query Qdrant. It answers ONLY using the provided `selected_text`.

### Generate Embeddings

```http
POST /api/rag/embed
Content-Type: application/json

{
  "texts": ["What is ROS 2?", "Explain URDF"],
  "input_type": "search_query"
}
```

### Document Ingestion

```http
POST /api/rag/ingest
Content-Type: application/json

{
  "docs_path": "./physical-ai-humanoid-robotics/docs"
}
```

### RAG Stats

```http
GET /api/rag/stats
```

Returns vector store info, embedding configuration, and chunk counts.

## Features

### RAG Chatbot
- Answers questions using book content
- Provides citations with relevance scores
- Supports multi-turn conversations
- Module-specific filtering

### Voice Input
- Browser-based audio recording
- OpenAI Whisper transcription
- Automatic intent detection
- Supports WAV, MP3, WebM formats

### Interactive Book
- Dark/light mode
- Mermaid diagrams
- LaTeX equations
- Code syntax highlighting
- Responsive design

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend type checking
cd physical-ai-humanoid-robotics
npm run typecheck
```

### Code Style

```bash
# Backend formatting
cd backend
black src/
isort src/

# Frontend linting
cd physical-ai-humanoid-robotics
npm run lint
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `COHERE_API_KEY` | Cohere API key for embeddings | Yes |
| `OPENAI_API_KEY` | OpenAI API key for chat | Yes |
| `DATABASE_URL` | Neon Postgres connection string | Yes |
| `QDRANT_URL` | Qdrant instance URL | Yes |
| `QDRANT_API_KEY` | Qdrant API key (cloud only) | No |
| `COHERE_EMBEDDING_MODEL` | Cohere model (default: embed-english-v3.0) | No |
| `OPENAI_CHAT_MODEL` | OpenAI model (default: gpt-4-turbo-preview) | No |
| `CHUNK_SIZE` | Document chunk size (default: 500) | No |
| `CORS_ORIGINS` | Allowed CORS origins | No |
| `DEBUG` | Enable debug mode | No |

## Technologies

- **Frontend**: Docusaurus 3, React 18, TypeScript
- **Backend**: FastAPI, Python 3.11, Pydantic v2
- **Embeddings**: Cohere embed-english-v3.0 (1024 dimensions)
- **Chat**: OpenAI GPT-4 Turbo
- **Vector DB**: Qdrant Cloud
- **Database**: Neon Serverless Postgres
- **Document Processing**: LangChain, python-frontmatter, BeautifulSoup
- **Deployment**: Docker, Vercel, Railway

## Success Criteria

- ✅ All 4 modules written in MDX and validated in Docusaurus
- ✅ All simulation and code examples reproducible
- ✅ Capstone agent supports: Voice → Plan → Navigate → Perceive → Manipulate
- ✅ RAG Chatbot answers book questions with grounded citations
- ✅ Deployment-ready for GitHub Pages + Railway

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Support

- 📖 [Documentation](https://physical-ai-robotics.github.io/physical-ai-humanoid-robotics/)
- 🐛 [Issues](https://github.com/physical-ai-robotics/physical-ai-humanoid-robotics/issues)
- 💬 [Discussions](https://github.com/physical-ai-robotics/physical-ai-humanoid-robotics/discussions)

---

Built with ❤️ for the Physical AI & Robotics community
