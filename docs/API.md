# API Documentation

Complete API reference for SkillFit AI Resume Matcher.

## Base URL

```
Production: https://api.skillfit-ai.com
Development: http://localhost:8000
```

## Authentication

All API endpoints (except health check and registration) require authentication.

### Methods

1. **API Key Header**
```bash
X-API-Key: your-api-key-here
```

2. **Bearer Token**
```bash
Authorization: Bearer your-jwt-token
```

## Endpoints

### Authentication

#### POST /api/v1/auth/register

Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response: 201 Created**
```json
{
  "id": 1,
  "email": "user@example.com",
  "api_key": "sk-abc123...",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### POST /api/v1/auth/login

Login and get JWT token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response: 200 OK**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### GET /api/v1/auth/me

Get current user information.

**Response: 200 OK**
```json
{
  "id": 1,
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Resumes

#### POST /api/v1/resumes/upload

Upload and parse a resume file.

**Request:**
- Method: `multipart/form-data`
- Fields:
  - `file`: Resume file (PDF, DOCX, or TXT)
  - `analyze`: boolean (optional, default: true)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/resumes/upload" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@resume.pdf" \
  -F "analyze=true"
```

**Response: 201 Created**
```json
{
  "id": 1,
  "filename": "resume.pdf",
  "file_type": "pdf",
  "raw_text": "John Doe\nSoftware Engineer...",
  "parsed_data": {
    "skills": ["Python", "FastAPI", "PostgreSQL"],
    "experience": {
      "total_years": 5,
      "roles": ["Software Engineer", "Backend Developer"]
    },
    "education": ["BS Computer Science"],
    "keywords": ["API", "databases", "cloud"],
    "summary": "Experienced backend engineer..."
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### GET /api/v1/resumes/

List all resumes for the current user.

**Query Parameters:**
- `skip`: int (default: 0)
- `limit`: int (default: 100, max: 100)

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "filename": "resume.pdf",
    "file_type": "pdf",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

#### GET /api/v1/resumes/{resume_id}

Get a specific resume by ID.

**Response: 200 OK**
```json
{
  "id": 1,
  "filename": "resume.pdf",
  "file_type": "pdf",
  "raw_text": "...",
  "parsed_data": {...},
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### DELETE /api/v1/resumes/{resume_id}

Delete a resume.

**Response: 204 No Content**

### Jobs

#### POST /api/v1/jobs/

Create a new job description.

**Request:**
```json
{
  "title": "Senior Backend Engineer",
  "company": "Tech Corp",
  "description": "We are seeking an experienced backend engineer...",
  "requirements": "5+ years of Python experience, FastAPI, PostgreSQL...",
  "source_url": "https://jobs.example.com/123"
}
```

**Query Parameters:**
- `analyze`: boolean (default: true) - Extract skills with LLM

**Response: 201 Created**
```json
{
  "id": 1,
  "title": "Senior Backend Engineer",
  "company": "Tech Corp",
  "description": "...",
  "requirements": "...",
  "parsed_data": {
    "technical_skills": {
      "required": ["Python", "FastAPI", "PostgreSQL"],
      "preferred": ["Docker", "AWS"]
    },
    "soft_skills": ["Communication", "Teamwork"],
    "experience_level": {
      "minimum_years": 5,
      "level": "senior"
    }
  },
  "is_active": true,
  "created_at": "2024-01-15T11:00:00Z"
}
```

#### GET /api/v1/jobs/

List all job descriptions.

**Query Parameters:**
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `active_only`: boolean (default: true)

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "title": "Senior Backend Engineer",
    "company": "Tech Corp",
    "is_active": true,
    "created_at": "2024-01-15T11:00:00Z"
  }
]
```

#### GET /api/v1/jobs/{job_id}

Get a specific job description.

**Response: 200 OK**

#### PUT /api/v1/jobs/{job_id}

Update a job description.

**Request:** Same as POST

**Response: 200 OK**

#### DELETE /api/v1/jobs/{job_id}

Delete a job description.

**Response: 204 No Content**

### Matches

#### POST /api/v1/matches/

Create a match between a resume and job.

**Request:**
```json
{
  "resume_id": 1,
  "job_id": 1,
  "detailed": true,
  "llm_provider": "claude",
  "llm_model": "claude-3-5-sonnet-20241022"
}
```

**Fields:**
- `resume_id`: int (required)
- `job_id`: int (required)
- `detailed`: boolean (default: true) - Detailed analysis vs quick match
- `llm_provider`: string (optional) - "claude", "openai", "gemini", "openai_compatible"
- `llm_model`: string (optional) - Specific model name

**Response: 201 Created**
```json
{
  "id": 1,
  "resume_id": 1,
  "job_id": 1,
  "match_score": 85.5,
  "missing_skills": [
    "Kubernetes",
    "GraphQL",
    "Microservices architecture"
  ],
  "recommendations": [
    "Consider learning Kubernetes for container orchestration",
    "Gain experience with GraphQL APIs",
    "Study microservices design patterns"
  ],
  "explanation": "The candidate demonstrates strong backend engineering skills with 5 years of Python experience and expertise in FastAPI and PostgreSQL. They have solid fundamentals in database design and API development. However, to be fully competitive for this senior role, they should develop skills in Kubernetes for production deployments and gain familiarity with GraphQL as an alternative to REST APIs. Their experience with Docker provides a good foundation for learning Kubernetes.",
  "llm_provider": "claude",
  "llm_model": "claude-3-5-sonnet-20241022",
  "tokens_used": 2450,
  "cost_estimate": 0.022,
  "created_at": "2024-01-15T12:00:00Z"
}
```

#### POST /api/v1/matches/batch

Match multiple resumes against a single job.

**Request:**
```json
{
  "resume_ids": [1, 2, 3, 4, 5],
  "job_id": 1,
  "detailed": false,
  "llm_provider": "claude"
}
```

**Response: 200 OK**
```json
[
  {
    "id": 1,
    "resume_id": 1,
    "match_score": 92.0,
    "created_at": "2024-01-15T12:00:00Z"
  },
  {
    "id": 2,
    "resume_id": 3,
    "match_score": 87.5,
    "created_at": "2024-01-15T12:00:05Z"
  }
]
```

#### GET /api/v1/matches/

List all matches.

**Query Parameters:**
- `resume_id`: int (optional) - Filter by resume
- `job_id`: int (optional) - Filter by job
- `min_score`: float (optional, 0-100) - Minimum match score
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response: 200 OK**

#### GET /api/v1/matches/{match_id}

Get a specific match.

**Response: 200 OK**

#### DELETE /api/v1/matches/{match_id}

Delete a match.

**Response: 204 No Content**

### Health

#### GET /api/v1/health

Health check endpoint (no authentication required).

**Response: 200 OK**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message description"
}
```

### Common Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `204 No Content`: Success with no response body
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `409 Conflict`: Duplicate resource
- `413 Payload Too Large`: File too large
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

Default limits (configurable):
- 60 requests per minute per user
- Burst allowance: 10 requests

When limit exceeded:
```json
{
  "detail": "Rate limit exceeded. Try again in 30 seconds."
}
```

## Pagination

List endpoints support pagination:

```
GET /api/v1/resumes/?skip=20&limit=10
```

## Cost Tracking

When `ENABLE_COST_TRACKING=True`, responses include:

```json
{
  "tokens_used": 2450,
  "cost_estimate": 0.022
}
```

Cost estimates are approximate and based on provider pricing:
- Claude: ~$9/million tokens
- OpenAI GPT-4: ~$20/million tokens
- Gemini: ~$1/million tokens

## Webhooks (Coming Soon)

Subscribe to events:
- `resume.uploaded`
- `match.completed`
- `batch.completed`

## SDK Examples

### Python

```python
import requests

class SkillFitClient:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

    def upload_resume(self, file_path: str) -> dict:
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{self.base_url}/api/v1/resumes/upload",
                headers=self.headers,
                files={"file": f},
                data={"analyze": "true"}
            )
        return response.json()

    def match(self, resume_id: int, job_id: int) -> dict:
        response = requests.post(
            f"{self.base_url}/api/v1/matches/",
            headers=self.headers,
            json={
                "resume_id": resume_id,
                "job_id": job_id,
                "detailed": True
            }
        )
        return response.json()
```

### JavaScript/TypeScript

```typescript
class SkillFitClient {
  constructor(
    private apiKey: string,
    private baseUrl: string = "http://localhost:8000"
  ) {}

  async uploadResume(file: File): Promise<Resume> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("analyze", "true");

    const response = await fetch(`${this.baseUrl}/api/v1/resumes/upload`, {
      method: "POST",
      headers: {
        "X-API-Key": this.apiKey,
      },
      body: formData,
    });

    return response.json();
  }

  async match(resumeId: number, jobId: number): Promise<Match> {
    const response = await fetch(`${this.baseUrl}/api/v1/matches/`, {
      method: "POST",
      headers: {
        "X-API-Key": this.apiKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        resume_id: resumeId,
        job_id: jobId,
        detailed: true,
      }),
    });

    return response.json();
  }
}
```

