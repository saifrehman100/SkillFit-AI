# Deployment Guide

This guide covers deploying SkillFit AI to various cloud platforms.

## Table of Contents

1. [Railway Deployment](#railway-deployment)
2. [Render Deployment](#render-deployment)
3. [Fly.io Deployment](#flyio-deployment)
4. [AWS Deployment](#aws-deployment)
5. [Environment Variables](#environment-variables)
6. [Post-Deployment](#post-deployment)

## Railway Deployment

Railway offers the simplest deployment with automatic PostgreSQL and Redis provisioning.

### Prerequisites

- Railway account: https://railway.app
- Railway CLI installed

### Steps

1. **Install Railway CLI**
```bash
npm install -g @railway/cli
```

2. **Login to Railway**
```bash
railway login
```

3. **Initialize Project**
```bash
cd skillfit-ai
railway init
```

4. **Add PostgreSQL**
```bash
railway add --database postgres
```

5. **Add Redis**
```bash
railway add --database redis
```

6. **Configure Environment Variables**

In Railway dashboard, add:
```
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
GOOGLE_API_KEY=your-key
```

7. **Deploy**
```bash
railway up
```

8. **Get Domain**
```bash
railway domain
```

### Railway Configuration

Create `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "backend/Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/v1/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## Render Deployment

### Prerequisites

- Render account: https://render.com
- GitHub repository

### Steps

1. **Create New Web Service**
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service**
```yaml
Name: skillfit-ai-backend
Environment: Docker
Region: Oregon (or closest to you)
Branch: main
Docker Build Context Directory: backend
Docker Command: (leave empty, uses Dockerfile CMD)
```

3. **Add PostgreSQL Database**
   - Click "New +" → "PostgreSQL"
   - Name: skillfit-ai-db
   - Copy database URL

4. **Add Redis Instance**
   - Click "New +" → "Redis"
   - Name: skillfit-ai-redis
   - Copy Redis URL

5. **Configure Environment Variables**

In Web Service settings → Environment:
```
DATABASE_URL=<postgres-url-from-render>
REDIS_URL=<redis-url-from-render>
CELERY_BROKER_URL=<redis-url>/1
CELERY_RESULT_BACKEND=<redis-url>/2
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
```

6. **Add Background Worker**

Create another service for Celery:
```yaml
Name: skillfit-ai-worker
Environment: Docker
Docker Command: celery -A app.tasks.celery_app worker --loglevel=info
```

7. **Deploy**
   - Click "Manual Deploy" or push to GitHub

## Fly.io Deployment

### Prerequisites

- Fly.io account: https://fly.io
- flyctl CLI installed

### Steps

1. **Install flyctl**
```bash
curl -L https://fly.io/install.sh | sh
```

2. **Login**
```bash
flyctl auth login
```

3. **Launch App**
```bash
cd skillfit-ai
flyctl launch
```

Answer the prompts:
```
? App Name: skillfit-ai
? Select region: (choose closest)
? Would you like to set up a PostgreSQL database? Yes
? Would you like to set up a Redis database? Yes
```

4. **Configure Dockerfile**

Create `fly.toml`:
```toml
app = "skillfit-ai"

[build]
  dockerfile = "backend/Dockerfile"

[env]
  PORT = "8000"

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"

[deploy]
  strategy = "rolling"
```

5. **Set Secrets**
```bash
flyctl secrets set ANTHROPIC_API_KEY=your-key
flyctl secrets set OPENAI_API_KEY=your-key
flyctl secrets set GOOGLE_API_KEY=your-key
```

6. **Deploy**
```bash
flyctl deploy
```

7. **Scale Workers**
```bash
flyctl scale count app=2 worker=2
```

## AWS Deployment

### Using ECS + RDS + ElastiCache

1. **Create RDS PostgreSQL Instance**
```bash
aws rds create-db-instance \
  --db-instance-identifier skillfit-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 16.1 \
  --master-username admin \
  --master-user-password your-password \
  --allocated-storage 20
```

2. **Create ElastiCache Redis**
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id skillfit-redis \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1
```

3. **Build and Push Docker Image**
```bash
# Create ECR repository
aws ecr create-repository --repository-name skillfit-ai

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t skillfit-ai backend/
docker tag skillfit-ai:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/skillfit-ai:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/skillfit-ai:latest
```

4. **Create ECS Task Definition**
```json
{
  "family": "skillfit-ai",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/skillfit-ai:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://..."
        }
      ],
      "secrets": [
        {
          "name": "ANTHROPIC_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:..."
        }
      ]
    }
  ]
}
```

5. **Create ECS Service**
```bash
aws ecs create-service \
  --cluster default \
  --service-name skillfit-api \
  --task-definition skillfit-ai \
  --desired-count 2 \
  --launch-type FARGATE \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:...
```

## Environment Variables

### Required Variables

```bash
# LLM API Keys (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379/0
CELERY_BROKER_URL=redis://host:6379/1
CELERY_RESULT_BACKEND=redis://host:6379/2

# Security
SECRET_KEY=your-secret-key-change-in-production
```

### Optional Variables

```bash
# Application
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
WORKERS=4

# LLM Defaults
DEFAULT_LLM_PROVIDER=claude
DEFAULT_MODEL_NAME=claude-3-5-sonnet-20241022
DEFAULT_TEMPERATURE=0.3

# Features
ENABLE_VECTOR_SEARCH=True
ENABLE_COST_TRACKING=True
ENABLE_METRICS=True

# Limits
MAX_UPLOAD_SIZE_MB=10
MAX_BATCH_SIZE=100
RATE_LIMIT_PER_MINUTE=60
```

## Post-Deployment

### 1. Run Database Migrations

```bash
# Railway
railway run alembic upgrade head

# Render (via Shell)
alembic upgrade head

# Fly.io
flyctl ssh console
alembic upgrade head
```

### 2. Create Admin User

```bash
curl -X POST "https://your-domain.com/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "secure-password"
  }'
```

### 3. Test Health Endpoint

```bash
curl https://your-domain.com/api/v1/health
```

### 4. Configure Domain (Optional)

**Railway:**
```bash
railway domain add yourdomain.com
```

**Render:**
- Go to Settings → Custom Domains
- Add your domain
- Update DNS records

**Fly.io:**
```bash
flyctl certs add yourdomain.com
```

### 5. Set Up Monitoring

**Sentry for Error Tracking:**
```bash
pip install sentry-sdk
```

In `app/main.py`:
```python
import sentry_sdk

sentry_sdk.init(
    dsn="your-sentry-dsn",
    environment=settings.environment
)
```

**Prometheus Metrics:**

Add to `docker-compose.yml`:
```yaml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"
```

### 6. Configure Backups

**PostgreSQL Backups (Railway):**
- Automatic daily backups
- Retention: 7 days (free) / 30 days (pro)

**Manual Backup:**
```bash
pg_dump $DATABASE_URL > backup.sql
```

## Troubleshooting

### Common Issues

**1. Database Connection Failed**
- Check `DATABASE_URL` format
- Verify database is running
- Check firewall rules

**2. Celery Worker Not Starting**
- Verify Redis connection
- Check `CELERY_BROKER_URL`
- Review worker logs

**3. Out of Memory**
- Increase container memory
- Reduce `MAX_BATCH_SIZE`
- Scale horizontally

**4. Slow Performance**
- Enable Redis caching
- Add database indexes
- Use connection pooling

### Health Checks

```bash
# API Health
curl https://your-domain.com/api/v1/health

# Database Connection
curl https://your-domain.com/api/v1/health | jq .db_status

# Celery Status
celery -A app.tasks.celery_app inspect active
```

## Support

For deployment issues:
- 📧 Email: devops@skillfit-ai.com
- 💬 Discord: https://discord.gg/skillfit
- 📖 Docs: https://docs.skillfit-ai.com
