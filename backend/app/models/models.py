"""
SQLAlchemy models for the application.
Includes support for pgvector for vector embeddings.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    func,
)
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.models.database import Base


class User(Base):
    """User model for API authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    api_key = Column(String(64), unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # LLM API Keys (encrypted in production)
    llm_api_keys = Column(JSON, nullable=True)  # Store user's own LLM API keys
    llm_provider = Column(String(50), nullable=True)  # User's preferred LLM provider
    llm_model = Column(String(100), nullable=True)  # User's preferred model name

    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    """Resume model for storing parsed resumes and metadata."""

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf, docx, txt
    raw_text = Column(Text, nullable=False)
    parsed_data = Column(JSON, nullable=True)  # Structured data from LLM analysis

    # Vector embedding for similarity search
    embedding = Column(Vector(1536), nullable=True)  # OpenAI embedding size

    # Metadata
    file_size = Column(Integer, nullable=True)
    upload_hash = Column(String(64), nullable=True, index=True)  # For deduplication
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="resumes")
    matches = relationship("Match", back_populates="resume", cascade="all, delete-orphan")

    # Indexes for vector similarity search
    __table_args__ = (
        Index("idx_resume_embedding", "embedding", postgresql_using="ivfflat"),
    )


class Job(Base):
    """Job description model."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    parsed_data = Column(JSON, nullable=True)  # Structured requirements

    # Vector embedding for similarity search
    embedding = Column(Vector(1536), nullable=True)

    # Metadata
    source_url = Column(Text, nullable=True)  # Changed from String(512) to Text for long URLs
    job_hash = Column(String(64), nullable=True, index=True)  # For deduplication
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="jobs")
    matches = relationship("Match", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_job_embedding", "embedding", postgresql_using="ivfflat"),
    )


class Match(Base):
    """Match results between resumes and jobs."""

    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)

    # Match results
    match_score = Column(Float, nullable=False)  # 0-100
    missing_skills = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)

    # LLM metadata
    llm_provider = Column(String(50), nullable=True)
    llm_model = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost_estimate = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="matches")
    resume = relationship("Resume", back_populates="matches")
    job = relationship("Job", back_populates="matches")
    application = relationship("Application", back_populates="match", uselist=False)

    # Indexes
    __table_args__ = (
        Index("idx_match_score", "match_score"),
        Index("idx_match_user_resume_job", "user_id", "resume_id", "job_id"),
    )


class Application(Base):
    """Application tracking for job applications."""

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)

    company = Column(String(255), nullable=False)
    position = Column(String(255), nullable=False)
    status = Column(String(50), default="wishlist")  # wishlist, applied, interview, offer, rejected

    application_date = Column(DateTime, nullable=True)
    job_url = Column(Text, nullable=True)  # Changed from String(500) to Text for long URLs
    notes = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    match = relationship("Match", back_populates="application")

    # Indexes
    __table_args__ = (
        Index("idx_application_user_status", "user_id", "status"),
        Index("idx_application_status", "status"),
    )


class BatchJob(Base):
    """Batch processing jobs for async operations."""

    __tablename__ = "batch_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_type = Column(String(50), nullable=False)  # resume_parse, match, etc.
    status = Column(
        String(20),
        nullable=False,
        default="pending"
    )  # pending, processing, completed, failed
    total_items = Column(Integer, nullable=False)
    processed_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)

    # Results
    results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Celery task ID
    celery_task_id = Column(String(255), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_batch_status", "status"),
        Index("idx_batch_user_status", "user_id", "status"),
    )


class APIUsage(Base):
    """Track API usage and costs for monitoring."""

    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    endpoint = Column(String(100), nullable=False)
    llm_provider = Column(String(50), nullable=True)
    llm_model = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost_estimate = Column(Float, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("idx_usage_user_created", "user_id", "created_at"),
        Index("idx_usage_endpoint", "endpoint"),
    )
