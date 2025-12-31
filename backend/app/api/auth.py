"""
Authentication endpoints for user registration and login.
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    LLMSettingsUpdate,
    LLMSettingsResponse,
    UsageResponse
)
from app.core.auth import (
    create_access_token,
    generate_api_key,
    get_current_user,
    get_password_hash,
    verify_password
)
from app.core.config import settings
from app.models.database import get_db
from app.models.models import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        api_key=generate_api_key()
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login and get access token.
    """
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    """
    return current_user


@router.post("/api-key/regenerate")
async def regenerate_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Regenerate API key for current user.
    """
    current_user.api_key = generate_api_key()
    db.commit()

    return {"api_key": current_user.api_key}


@router.get("/llm-settings", response_model=LLMSettingsResponse)
async def get_llm_settings(current_user: User = Depends(get_current_user)):
    """
    Get user's LLM preferences.
    System manages API keys - users just select their preferred provider/model.
    """
    # Check which providers have API keys configured
    available_providers = []
    if settings.google_api_key:
        available_providers.append("gemini")
    if settings.openai_api_key:
        available_providers.append("openai")
    if settings.anthropic_api_key:
        available_providers.append("claude")
    if settings.openai_compatible_api_key and settings.openai_compatible_base_url:
        available_providers.append("openai_compatible")

    return LLMSettingsResponse(
        provider=current_user.llm_provider,
        model=current_user.llm_model,
        available_providers=available_providers
    )


@router.put("/llm-settings", response_model=LLMSettingsResponse)
async def update_llm_settings(
    settings_data: LLMSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user's LLM preferences.
    System manages API keys - users only select provider/model preference.
    """
    # Check which providers have API keys configured
    available_providers = []
    if settings.google_api_key:
        available_providers.append("gemini")
    if settings.openai_api_key:
        available_providers.append("openai")
    if settings.anthropic_api_key:
        available_providers.append("claude")
    if settings.openai_compatible_api_key and settings.openai_compatible_base_url:
        available_providers.append("openai_compatible")

    # Update provider if provided
    if settings_data.provider is not None:
        # Validate that the provider has an API key configured
        if settings_data.provider not in available_providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider '{settings_data.provider}' is not configured. Available providers: {', '.join(available_providers)}"
            )
        current_user.llm_provider = settings_data.provider

    # Update model if provided
    if settings_data.model is not None:
        current_user.llm_model = settings_data.model

    db.commit()
    db.refresh(current_user)

    return LLMSettingsResponse(
        provider=current_user.llm_provider,
        model=current_user.llm_model,
        available_providers=available_providers
    )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(current_user: User = Depends(get_current_user)):
    """
    Get user's usage statistics and plan information.
    """
    # Define plan limits
    PLAN_LIMITS = {
        "free": 3,
        "pro": 999999,  # Unlimited for pro
        "enterprise": 999999
    }

    limit = PLAN_LIMITS.get(current_user.plan, 3)
    remaining = max(0, limit - current_user.matches_used)

    return UsageResponse(
        plan=current_user.plan,
        matches_used=current_user.matches_used,
        matches_limit=limit,
        matches_remaining=remaining,
        can_create_match=remaining > 0
    )
