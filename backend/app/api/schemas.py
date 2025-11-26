"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, EmailStr, Field, field_validator


# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    is_active: bool
    created_at: datetime
    api_key: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Resume schemas
class ResumeUpload(BaseModel):
    analyze: bool = Field(default=True, description="Run LLM analysis on upload")


class ResumeResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    raw_text: str
    parsed_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Job schemas
class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    description: str = Field(min_length=1)
    requirements: Optional[str] = None
    source_url: Optional[str] = None


class JobResponse(BaseModel):
    id: int
    title: str
    company: Optional[str]
    description: str
    requirements: Optional[str]
    parsed_data: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Match schemas
class MatchRequest(BaseModel):
    resume_id: int
    job_id: int
    detailed: bool = Field(
        default=True,
        description="If True, provide detailed analysis. If False, quick match."
    )
    llm_provider: Optional[str] = Field(
        None,
        description="LLM provider to use (claude, openai, gemini, openai_compatible)"
    )
    llm_model: Optional[str] = Field(None, description="Specific model to use")


class BatchMatchRequest(BaseModel):
    resume_ids: List[int] = Field(..., min_length=1, max_length=100)
    job_id: int
    detailed: bool = False
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None


class MatchResponse(BaseModel):
    id: int
    resume_id: int
    job_id: int
    match_score: float
    missing_skills: Optional[List[str]]
    recommendations: Optional[List[str]]
    explanation: Optional[str]
    llm_provider: Optional[str]
    llm_model: Optional[str]
    tokens_used: Optional[int]
    cost_estimate: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# Batch job schemas
class BatchJobResponse(BaseModel):
    id: int
    job_type: str
    status: str
    total_items: int
    processed_items: int
    failed_items: int
    results: Optional[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# LLM config schemas
class LLMConfig(BaseModel):
    provider: str = Field(
        default="claude",
        description="LLM provider (claude, openai, gemini, openai_compatible)"
    )
    model: Optional[str] = Field(None, description="Specific model name")
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=32000)


# Search schemas
class ResumeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=10, ge=1, le=100)
    min_score: float = Field(default=0.5, ge=0.0, le=1.0)


class JobSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=10, ge=1, le=100)
    min_score: float = Field(default=0.5, ge=0.0, le=1.0)


# Health check
class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    timestamp: datetime
