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
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    plan: str = "free"
    matches_used: int = 0

    class Config:
        from_attributes = True


class LLMSettingsUpdate(BaseModel):
    """Schema for updating user's LLM preferences (system manages API keys)."""
    provider: Optional[str] = Field(
        None,
        description="LLM provider (gemini, openai, claude, openai_compatible)"
    )
    model: Optional[str] = Field(None, description="Specific model name to use")


class LLMSettingsResponse(BaseModel):
    """Response for user's LLM settings."""
    provider: Optional[str] = None
    model: Optional[str] = None
    available_providers: List[str] = ["gemini", "openai", "claude", "openai_compatible"]


class UsageResponse(BaseModel):
    """Response for user's usage statistics."""
    plan: str
    matches_used: int
    matches_limit: int
    matches_remaining: int
    can_create_match: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class ProPlanInterestRequest(BaseModel):
    """Request to express interest in Pro plan."""
    email: EmailStr
    feature_interested_in: Optional[str] = None  # What feature brought them here


class ContactSalesRequest(BaseModel):
    """Request to contact sales for Enterprise plan."""
    email: EmailStr
    plan: str = "Enterprise"
    message: Optional[str] = None


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
    recommendations: Optional[List[Any]]  # Can be List[str] (old format) or List[Dict] (new format with action, priority, impact_estimate, reason)
    explanation: Optional[str]
    llm_provider: Optional[str]
    llm_model: Optional[str]
    created_at: datetime
    # ATS Analysis fields
    ats_score: Optional[float] = None
    keyword_matches: Optional[Dict[str, Any]] = None
    ats_issues: Optional[Dict[str, Any]] = None
    # Cached generated content
    interview_prep_data: Optional[Dict[str, Any]] = None
    cover_letter_data: Optional[Dict[str, Any]] = None
    improved_resume_data: Optional[Dict[str, Any]] = None
    # Note: tokens_used and cost_estimate are stored in DB but not exposed to users

    class Config:
        from_attributes = True


# Application schemas
class ApplicationCreate(BaseModel):
    job_id: Optional[int] = None
    match_id: Optional[int] = None
    company: str = Field(min_length=1, max_length=255)
    position: str = Field(min_length=1, max_length=255)
    status: str = Field(
        default="wishlist",
        pattern="^(wishlist|applied|interview|offer|rejected)$"
    )
    application_date: Optional[datetime] = None
    job_url: Optional[str] = None  # Removed max_length constraint for long URLs
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = Field(
        None,
        pattern="^(wishlist|applied|interview|offer|rejected)$"
    )
    application_date: Optional[datetime] = None
    job_url: Optional[str] = None
    notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    job_id: Optional[int]
    match_id: Optional[int]
    company: str
    position: str
    status: str
    application_date: Optional[datetime]
    job_url: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Nested data (optional)
    job: Optional[JobResponse] = None
    match: Optional[MatchResponse] = None

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
