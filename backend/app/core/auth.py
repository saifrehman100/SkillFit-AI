"""
Authentication and authorization utilities.
Supports API key-based authentication for users with their own LLM API keys.
"""
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import get_db
from app.models.models import User

# Skip passlib's wrap bug detection for bcrypt 4.x compatibility
os.environ["PASSLIB_SKIP_CHECKS"] = "1"

# Password hashing
# Configure bcrypt to not truncate and handle password length ourselves
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b",  # Use bcrypt 2b variant
    bcrypt__rounds=12,   # Set rounds explicitly
    bcrypt__truncate_error=True,  # Enable truncate error handling
)

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    # Truncate password to 72 bytes for bcrypt compatibility
    # Convert to bytes, truncate, then back to string
    password_bytes = plain_password.encode('utf-8')[:72]
    plain_password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    # Truncate password to 72 bytes for bcrypt compatibility
    # Convert to bytes, truncate, then back to string
    password_bytes = password.encode('utf-8')[:72]
    password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


async def get_current_user_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token."""
    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_current_user_from_api_key(
    api_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from API key."""
    if not api_key:
        return None

    user = db.query(User).filter(User.api_key == api_key).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def get_current_user(
    token_user: Optional[User] = Depends(get_current_user_from_token),
    api_key_user: Optional[User] = Depends(get_current_user_from_api_key),
) -> User:
    """
    Get current user from either JWT token or API key.
    Prioritizes API key if both are provided.
    """
    if api_key_user:
        return api_key_user
    if token_user:
        return token_user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated"
    )


def get_user_llm_api_key(user: User, provider: str) -> Optional[str]:
    """
    Get system LLM API key for a specific provider.
    System manages all API keys - users only select their preferred provider.
    """
    # Always use system config (SaaS model - we manage the keys)
    provider_keys = {
        "claude": settings.anthropic_api_key,
        "openai": settings.openai_api_key,
        "gemini": settings.google_api_key,
        "openai_compatible": settings.openai_compatible_api_key,
    }

    return provider_keys.get(provider)
