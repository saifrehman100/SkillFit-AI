# Local Setup Guide (Without Docker)

This guide helps you run SkillFit AI locally without Docker.

## Quick Start (Simplified - Using SQLite)

This gets you running in ~5 minutes without PostgreSQL/Redis setup.

### Step 1: Set Up Python Environment

```bash
cd /Users/saif/SkillFit-AI/backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2: Configure for Local Development

Create `.env` file:
```bash
cp ../.env.example .env
```

Edit `.env` with these LOCAL settings:
```bash
# Use SQLite instead of PostgreSQL for local dev
DATABASE_URL=sqlite:///./skillfit.db

# Use memory backend for Celery (no Redis needed for quick testing)
CELERY_BROKER_URL=memory://
CELERY_RESULT_BACKEND=cache+memory://

# Add at least one LLM API key
ANTHROPIC_API_KEY=your-key-here
# OR
OPENAI_API_KEY=your-key-here
# OR
GOOGLE_API_KEY=your-key-here

# Other settings
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
ENABLE_VECTOR_SEARCH=False  # Disable pgvector features
```

### Step 3: Initialize Database

```bash
# Create database tables (SQLite - no server needed!)
python -c "from app.models.database import Base, engine; Base.metadata.create_all(engine)"
```

### Step 4: Start the Application

```bash
# Start FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Test It!

Open another terminal and test:

```bash
# Health check
curl http://localhost:8000/api/v1/health

# View API docs
open http://localhost:8000/docs
```

## Full Setup (With PostgreSQL + Redis)

If you want the full production setup locally, continue here...

### Install Redis

```bash
brew install redis
brew services start redis

# Test it
redis-cli ping
# Should return: PONG
```

### Install PostgreSQL with pgvector

```bash
# Reinstall PostgreSQL (fresh start)
brew install postgresql@16

# Install pgvector
brew install pgvector

# Start PostgreSQL
brew services start postgresql@16

# Create database
createdb resume_matcher

# Enable pgvector extension
psql resume_matcher -c "CREATE EXTENSION vector;"
```

### Update .env for Full Setup

```bash
DATABASE_URL=postgresql://$(whoami)@localhost:5432/resume_matcher
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
ENABLE_VECTOR_SEARCH=True
```

### Start All Services

Terminal 1 - API Server:
```bash
cd /Users/saif/SkillFit-AI/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Terminal 2 - Celery Worker:
```bash
cd /Users/saif/SkillFit-AI/backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info
```

Terminal 3 - Celery Flower (Optional - Monitoring):
```bash
cd /Users/saif/SkillFit-AI/backend
source venv/bin/activate
celery -A app.tasks.celery_app flower --port=5555
```

## Testing Your Setup

```bash
# Activate virtual environment
cd /Users/saif/SkillFit-AI/backend
source venv/bin/activate

# Run tests
pytest

# Run with coverage
pytest --cov=app
```

## Common Issues

### "ModuleNotFoundError"
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### "Database connection error"
```bash
# Check if using SQLite (simpler)
# In .env: DATABASE_URL=sqlite:///./skillfit.db

# OR check PostgreSQL is running
brew services list | grep postgresql
```

### "Redis connection error"
```bash
# For quick testing, use memory backend
# In .env:
CELERY_BROKER_URL=memory://
CELERY_RESULT_BACKEND=cache+memory://

# OR start Redis
brew services start redis
```

## Next Steps

Once running:
1. Visit http://localhost:8000/docs - Interactive API documentation
2. Create a user account
3. Upload a resume
4. Create a job description
5. Match them!

## Switching from SQLite to PostgreSQL Later

When you're ready for full features:

1. Install PostgreSQL + pgvector (see above)
2. Update `.env` with PostgreSQL URL
3. Run migrations:
   ```bash
   alembic upgrade head
   ```
4. Restart the application
