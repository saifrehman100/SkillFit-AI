"""
Pytest configuration and fixtures for testing.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.database import Base, get_db
from app.models.models import User
from app.core.auth import get_password_hash, generate_api_key

# Test database URL (use in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        api_key=generate_api_key(),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for test user."""
    return {"X-API-Key": test_user.api_key}


@pytest.fixture
def sample_resume_text():
    """Sample resume text for testing."""
    return """
John Doe
Software Engineer

EXPERIENCE:
- 5 years as Senior Software Engineer at Tech Corp
- 3 years as Software Developer at StartupXYZ

SKILLS:
Python, JavaScript, React, FastAPI, PostgreSQL, Docker, AWS

EDUCATION:
Bachelor of Science in Computer Science
University of Technology, 2015
"""


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
Senior Backend Engineer

Requirements:
- 5+ years of experience in backend development
- Strong proficiency in Python and FastAPI
- Experience with PostgreSQL and Redis
- Knowledge of Docker and cloud platforms (AWS/GCP)
- Excellent problem-solving skills

Preferred:
- Experience with microservices architecture
- Familiarity with Celery for task queuing
"""
