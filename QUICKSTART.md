# Quick Start Guide

Get SkillFit AI up and running in 5 minutes!

## Prerequisites

- Docker & Docker Compose
- At least one LLM API key (Claude, OpenAI, or Gemini)

## Option 1: Automated Setup (Recommended)

```bash
# Clone repository
git clone https://github.com/yourusername/skillfit-ai.git
cd skillfit-ai

# Run setup script
./scripts/setup.sh

# Run demo
python scripts/demo.py
```

The setup script will:
1. ✅ Create `.env` from template
2. ✅ Build Docker containers
3. ✅ Start all services
4. ✅ Run database migrations
5. ✅ Create sample admin user

## Option 2: Manual Setup

### Step 1: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your favorite editor
```

Required variables:
```bash
# At least one LLM API key
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Database (auto-configured by docker-compose)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/resume_matcher
REDIS_URL=redis://redis:6379/0
```

### Step 2: Start Services

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### Step 3: Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head
```

### Step 4: Test API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Should return:
# {"status":"healthy","version":"1.0.0",...}
```

## Your First Match

### 1. Register User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@example.com",
    "password": "securepassword123"
  }'
```

Save the returned `api_key`!

### 2. Upload Resume

```bash
curl -X POST "http://localhost:8000/api/v1/resumes/upload" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@your_resume.pdf" \
  -F "analyze=true"
```

Note the returned `resume_id`.

### 3. Create Job

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Software Engineer",
    "company": "Your Company",
    "description": "Job description here...",
    "requirements": "Requirements here..."
  }'
```

Note the returned `job_id`.

### 4. Match Resume to Job

```bash
curl -X POST "http://localhost:8000/api/v1/matches/" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": 1,
    "job_id": 1,
    "detailed": true
  }'
```

You'll get:
- Match score (0-100)
- Missing skills
- Recommendations
- Detailed explanation

## Explore the API

### Interactive Documentation

Visit http://localhost:8000/docs for:
- Complete API reference
- Try out endpoints interactively
- See request/response examples

### Key Endpoints

```
POST /api/v1/auth/register       - Register new user
POST /api/v1/auth/login          - Login
POST /api/v1/resumes/upload      - Upload resume
GET  /api/v1/resumes/            - List resumes
POST /api/v1/jobs/               - Create job
GET  /api/v1/jobs/               - List jobs
POST /api/v1/matches/            - Create match
POST /api/v1/matches/batch       - Batch match
```

## Useful Commands

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f celery-worker

# Check service status
docker-compose ps

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Stop and remove all data
docker-compose down -v

# Run tests
docker-compose exec backend pytest

# Access backend shell
docker-compose exec backend bash

# Access database
docker-compose exec postgres psql -U postgres -d resume_matcher

# Monitor Celery tasks
# Open: http://localhost:5555
```

## Common Issues

### "Connection refused"

```bash
# Check if services are running
docker-compose ps

# Restart services
docker-compose restart

# Check logs
docker-compose logs backend
```

### "API key not configured"

Add your LLM API keys to `.env`:
```bash
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
```

Then restart:
```bash
docker-compose restart backend
```

### "Database connection failed"

```bash
# Check postgres is running
docker-compose ps postgres

# Restart postgres
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### "Out of memory"

Increase Docker memory:
- Docker Desktop → Settings → Resources → Memory → 4GB+

## Production Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for:
- Railway deployment
- Render deployment
- Fly.io deployment
- AWS deployment

## Next Steps

1. ✅ Read the [API Documentation](docs/API.md)
2. ✅ Check out the [Demo Script](scripts/demo.py)
3. ✅ Try batch matching multiple resumes
4. ✅ Experiment with different LLM providers
5. ✅ Deploy to production

## Support

- 📖 Documentation: [README.md](README.md)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/skillfit-ai/issues)
- 💬 Discord: https://discord.gg/skillfit
- 📧 Email: support@skillfit-ai.com

Happy matching! 🎯
