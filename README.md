# SkillFit AI - Resume & Job Match Scoring System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-ready AI-powered system for matching resumes to job descriptions using multiple LLM providers (Claude, OpenAI, Gemini). Built with FastAPI, PostgreSQL, and Celery for scalable async processing.

## 🚀 Features

### Core Capabilities
- **🔗 LinkedIn Integration**: Instantly scan LinkedIn job postings with your resume - no auth required!
- **🤖 Multi-LLM Support**: Choose between Claude, OpenAI GPT-4, Google Gemini, or any OpenAI-compatible API
- **📄 Resume Analysis**: Parse PDFs, DOCX, and TXT files with AI-powered skill extraction
- **🎯 Intelligent Matching**: Get detailed match scores (0-100) with missing skills and personalized recommendations
- **🔍 Vector Search**: Find similar resumes or jobs using semantic embeddings (pgvector)
- **⚡ Batch Processing**: Handle multiple resumes asynchronously with Celery
- **🌐 API-First Design**: RESTful API with automatic OpenAPI/Swagger documentation
- **🔐 User Authentication**: Flexible auth with API key support and user-specific LLM keys
- **💰 Cost Tracking**: Monitor API usage and cost estimates per request
- **🚀 Production Ready**: Docker support for deployment on Railway, Render, Fly.io, or any cloud platform

### What Makes This Special
✨ **One-Click Job Scanning**: Upload resume + LinkedIn URL → Get instant AI-powered match analysis
🎨 **Flexible LLM Options**: Bring your own API key or use system defaults
📊 **Detailed Insights**: Match scores, missing skills, strengths, weaknesses, and actionable recommendations
🔓 **No Account Required**: Public endpoints for instant testing and demos

## 📋 Table of Contents

- [Technology Stack](#technology-stack)
- [LinkedIn Integration Demo](#linkedin-integration-demo)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Development](#development)
- [Testing](#testing)
- [Configuration](#configuration)
- [Examples](#examples)
- [License](#license)

## 🛠 Technology Stack

**Frontend**
- Next.js 14 (App Router) - React framework with SSR/CSR
- TypeScript - Type-safe development
- Tailwind CSS - Utility-first styling with dark mode
- shadcn/ui - Radix UI primitives for components
- SWR - Data fetching and caching
- Recharts - Match score visualization
- React Dropzone - File upload interface

**Backend Framework**
- FastAPI (Python 3.11+) - High-performance async API framework
- Pydantic - Data validation and settings management
- SQLAlchemy - ORM for database operations

**AI & LLM Integration**
- OpenAI GPT-4/GPT-4-Turbo - Primary language model
- Anthropic Claude 3.5 Sonnet - Alternative LLM option
- Google Gemini 1.5 Pro - Multi-modal AI support
- Custom OpenAI-compatible APIs support

**Data & Processing**
- PostgreSQL 16 + pgvector - Vector similarity search
- Redis - Caching and message broker
- Celery - Distributed task queue for batch processing

**Document Processing**
- PyMuPDF (fitz) - PDF parsing
- python-docx - DOCX file handling
- BeautifulSoup4 - Web scraping (LinkedIn integration)

**DevOps & Deployment**
- Docker & Docker Compose - Containerization
- GitHub Actions - CI/CD pipeline
- Uvicorn - ASGI server
- Gunicorn - Production server

## 🔗 LinkedIn Integration Demo

Our standout feature! Scan any LinkedIn job posting with your resume in seconds:

```bash
# Example: Quick job match from LinkedIn URL
curl -X POST "http://localhost:8000/api/v1/linkedin/scan-job" \
  -F "linkedin_url=https://www.linkedin.com/jobs/view/3234567890" \
  -F "resume=@your_resume.pdf" \
  -F "llm_provider=openai" \
  -F "llm_model=gpt-4-turbo"
```

**Response includes:**
```json
{
  "success": true,
  "job": {
    "title": "Senior Software Engineer",
    "company": "Tech Corp",
    "location": "San Francisco, CA"
  },
  "match": {
    "score": 87,
    "missing_skills": ["Kubernetes", "GraphQL"],
    "recommendations": [
      "Add Kubernetes certification to stand out",
      "Highlight your Docker experience more prominently"
    ],
    "strengths": ["8+ years Python experience", "FastAPI expertise"],
    "weaknesses": ["Limited GraphQL experience"],
    "explanation": "Strong match! Your Python and FastAPI skills align perfectly..."
  },
  "metadata": {
    "llm_provider": "openai",
    "llm_model": "gpt-4-turbo",
    "tokens_used": 2547,
    "cost_estimate": "$0.025"
  }
}
```

**No authentication required** - Perfect for demos and portfolio showcasing!

## 🏃 Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- OR: Python 3.11+ and Node.js 20+ for local development
- PostgreSQL 16+ with pgvector extension
- Redis (for Celery)

### Option 1: Docker Compose - Full Stack (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/skillfit-ai.git
cd skillfit-ai
```

2. **Create `.env` file**
```bash
cp .env.example .env
# Edit .env and add your LLM API keys
```

3. **Start all services (Backend + Frontend + Database)**
```bash
docker-compose up -d
```

4. **Access the application**
- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Celery Flower**: http://localhost:5555

### Option 2: Development Mode with Hot Reload

For frontend development with live reload:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Option 3: Local Development (Backend Only)

1. **Install dependencies**
```bash
cd backend
pip install -r requirements.txt
```

2. **Set up PostgreSQL with pgvector**
```bash
# Install PostgreSQL and pgvector extension
# Then create database:
createdb resume_matcher
psql resume_matcher -c "CREATE EXTENSION vector;"
```

3. **Start Redis**
```bash
redis-server
```

4. **Run migrations**
```bash
alembic upgrade head
```

5. **Start the application**
```bash
# Terminal 1: API Server
uvicorn app.main:app --reload

# Terminal 2: Celery Worker
celery -A app.tasks.celery_app worker --loglevel=info

# Terminal 3 (optional): Celery Beat
celery -A app.tasks.celery_app beat --loglevel=info
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Applications                   │
│              (Web, Mobile, CLI, Jupyter)                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Auth    │  │ Resumes  │  │   Jobs   │             │
│  │ Endpoints│  │Endpoints │  │Endpoints │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Matches  │  │  Search  │  │  Batch   │             │
│  │Endpoints │  │Endpoints │  │Endpoints │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└────────────┬───────────────────────────┬────────────────┘
             │                           │
             ▼                           ▼
┌────────────────────┐       ┌────────────────────┐
│  PostgreSQL +      │       │  Redis + Celery    │
│    pgvector        │       │  (Async Tasks)     │
│                    │       │                    │
│  • Users           │       │  • Resume parsing  │
│  • Resumes         │       │  • Batch matching  │
│  • Jobs            │       │  • Embeddings      │
│  • Matches         │       │                    │
│  • Embeddings      │       └────────────────────┘
└────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│                    LLM Providers                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Anthropic│  │  OpenAI  │  │  Google  │             │
│  │  Claude  │  │  GPT-4   │  │  Gemini  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

### Key Components

- **FastAPI**: High-performance async API framework
- **PostgreSQL + pgvector**: Database with vector similarity search
- **Celery**: Distributed task queue for batch processing
- **Redis**: Caching and Celery message broker
- **Multi-LLM System**: Pluggable architecture for different AI providers

## 📚 API Documentation

### Authentication

All endpoints require authentication via API key or JWT token.

**Register a new user:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "api_key": "sk-abc123...",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Upload Resume

```bash
curl -X POST "http://localhost:8000/api/v1/resumes/upload" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@resume.pdf" \
  -F "analyze=true"
```

### Create Job Description

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Backend Engineer",
    "company": "Tech Corp",
    "description": "We are looking for...",
    "requirements": "5+ years experience..."
  }'
```

### Match Resume to Job

```bash
curl -X POST "http://localhost:8000/api/v1/matches/" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": 1,
    "job_id": 1,
    "detailed": true,
    "llm_provider": "claude"
  }'
```

**Response:**
```json
{
  "id": 1,
  "match_score": 85.5,
  "missing_skills": ["Kubernetes", "GraphQL"],
  "recommendations": [
    "Consider learning Kubernetes for container orchestration",
    "Add GraphQL experience to strengthen backend skills"
  ],
  "explanation": "The candidate shows strong alignment with the role...",
  "tokens_used": 2450,
  "cost_estimate": 0.022
}
```

### Batch Match Multiple Resumes

```bash
curl -X POST "http://localhost:8000/api/v1/matches/batch" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_ids": [1, 2, 3, 4, 5],
    "job_id": 1,
    "detailed": false
  }'
```

## 🚢 Deployment

### Railway

1. **Install Railway CLI**
```bash
npm i -g @railway/cli
```

2. **Deploy**
```bash
railway login
railway init
railway add --database postgres
railway add --database redis
railway up
```

3. **Set environment variables**
```bash
railway variables set ANTHROPIC_API_KEY=your-key
railway variables set OPENAI_API_KEY=your-key
```

### Render

1. Create a new Web Service
2. Connect your GitHub repository
3. Set build command: `docker build -t backend ./backend`
4. Add PostgreSQL and Redis services
5. Configure environment variables

### Fly.io

1. **Install flyctl**
```bash
curl -L https://fly.io/install.sh | sh
```

2. **Deploy**
```bash
fly launch
fly deploy
```

## 🛠️ Development

### Project Structure

```
skillfit-ai/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── resumes.py
│   │   │   ├── jobs.py
│   │   │   └── matches.py
│   │   ├── core/          # Core config
│   │   │   ├── config.py
│   │   │   ├── auth.py
│   │   │   ├── llm_providers.py
│   │   │   └── logging_config.py
│   │   ├── models/        # Database models
│   │   │   ├── database.py
│   │   │   └── models.py
│   │   ├── services/      # Business logic
│   │   │   ├── resume_parser.py
│   │   │   ├── job_matcher.py
│   │   │   └── vector_search.py
│   │   ├── tasks/         # Celery tasks
│   │   │   ├── celery_app.py
│   │   │   ├── resume_tasks.py
│   │   │   └── match_tasks.py
│   │   ├── utils/         # Utilities
│   │   │   └── embeddings.py
│   │   └── main.py        # FastAPI app
│   ├── tests/             # Test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/              # Optional UI
├── docs/                  # Documentation
├── docker-compose.yml
└── README.md
```

### Adding a New LLM Provider

1. **Create client class** in `app/core/llm_providers.py`:

```python
class NewLLMClient(BaseLLMClient):
    def get_default_model(self) -> str:
        return "model-name"

    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        # Implementation
        pass

    def estimate_cost(self, tokens: int) -> float:
        return (tokens / 1_000_000) * cost_per_million
```

2. **Register in factory**:

```python
LLMProvider.NEW_LLM = "new_llm"
clients[LLMProvider.NEW_LLM] = NewLLMClient
```

## 🧪 Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

Expected coverage: >80%

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Default LLM
DEFAULT_LLM_PROVIDER=claude
DEFAULT_MODEL_NAME=claude-3-5-sonnet-20241022
DEFAULT_TEMPERATURE=0.3

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/resume_matcher

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1

# Features
ENABLE_VECTOR_SEARCH=True
ENABLE_COST_TRACKING=True
MAX_UPLOAD_SIZE_MB=10
```

## 📊 Examples

### Python SDK Usage

```python
import requests

API_KEY = "your-api-key"
BASE_URL = "http://localhost:8000"

# Upload resume
with open("resume.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/api/v1/resumes/upload",
        headers={"X-API-Key": API_KEY},
        files={"file": f},
        data={"analyze": "true"}
    )
    resume = response.json()

# Create job
job_response = requests.post(
    f"{BASE_URL}/api/v1/jobs/",
    headers={"X-API-Key": API_KEY},
    json={
        "title": "Software Engineer",
        "description": "..."
    }
)
job = job_response.json()

# Match
match_response = requests.post(
    f"{BASE_URL}/api/v1/matches/",
    headers={"X-API-Key": API_KEY},
    json={
        "resume_id": resume["id"],
        "job_id": job["id"],
        "detailed": True
    }
)
match = match_response.json()
print(f"Match Score: {match['match_score']}/100")
```

### Jupyter Notebook

See `docs/demo_notebook.ipynb` for interactive examples.

## 📈 Performance

- **API Response Time**: ~200-500ms for simple matches
- **Detailed Match Analysis**: ~2-5s (depends on LLM)
- **Batch Processing**: 100 resumes in ~2-3 minutes
- **Vector Search**: <100ms for similarity queries

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure tests pass: `pytest`
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Anthropic Claude](https://www.anthropic.com/), [OpenAI](https://openai.com/), and [Google Gemini](https://deepmind.google/technologies/gemini/)
- Vector search with [pgvector](https://github.com/pgvector/pgvector)

## 📞 Support

- 📧 Email: saif.rehman2498@gmail.com

---

**Made with ❤️ by the SkillFit AI Team**
