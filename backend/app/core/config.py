"""
Application configuration using Pydantic settings.
Supports environment-based configuration (dev, staging, prod).
"""
from typing import Literal, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = Field(default="SkillFit AI - Resume Matcher")
    app_version: str = Field(default="1.0.0")
    environment: Literal["development", "staging", "production"] = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=4)

    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/resume_matcher"
    )
    database_pool_size: int = Field(default=10)
    database_max_overflow: int = Field(default=20)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # Authentication
    secret_key: str = Field(default="change-this-secret-key-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)

    # LLM API Keys
    anthropic_api_key: Optional[str] = Field(default=None)
    openai_api_key: Optional[str] = Field(default=None)
    google_api_key: Optional[str] = Field(default=None)
    openai_compatible_base_url: Optional[str] = Field(default=None)
    openai_compatible_api_key: Optional[str] = Field(default=None)

    # Default LLM Settings
    default_llm_provider: Literal["claude", "openai", "gemini", "openai_compatible"] = Field(
        default="claude"
    )
    default_model_name: str = Field(default="claude-3-5-sonnet-20241022")
    default_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    default_max_tokens: int = Field(default=4096, ge=1, le=32000)

    # Embeddings
    embeddings_provider: Literal["openai", "sentence_transformers"] = Field(default="openai")
    embeddings_model: str = Field(default="text-embedding-3-small")
    embeddings_dimensions: int = Field(default=1536)

    # Vector Database
    enable_vector_search: bool = Field(default=True)

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)
    rate_limit_burst: int = Field(default=10)

    # File Upload
    max_upload_size_mb: int = Field(default=10)
    allowed_extensions: str = Field(default="pdf,docx,txt")

    # Batch Processing
    max_batch_size: int = Field(default=100)
    batch_timeout_seconds: int = Field(default=300)

    # Cost Tracking
    enable_cost_tracking: bool = Field(default=True)

    # Monitoring
    enable_metrics: bool = Field(default=True)
    metrics_port: int = Field(default=9090)

    # Cloud Storage (GCP)
    gcp_project_id: Optional[str] = Field(default=None)
    gcp_bucket_name: Optional[str] = Field(default=None)
    gcs_credentials_json: Optional[str] = Field(default=None)

    @field_validator("allowed_extensions")
    @classmethod
    def parse_extensions(cls, v: str) -> list[str]:
        """Parse comma-separated extensions into a list."""
        return [ext.strip().lower() for ext in v.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def max_upload_size_bytes(self) -> int:
        """Get max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024


# Global settings instance
settings = Settings()
