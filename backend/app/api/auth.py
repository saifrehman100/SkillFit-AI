"""
Authentication endpoints for user registration and login.
"""
from datetime import datetime, timedelta
from jose import JWTError, jwt
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.api.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    LLMSettingsUpdate,
    LLMSettingsResponse,
    UsageResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ProPlanInterestRequest,
    ContactSalesRequest,
    UserFeedbackRequest
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
from app.services.email_service import email_service
from app.services.oauth_service import OAuthService

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
        "free": 10,  # 10 free job matches
        "pro": 999999,  # Unlimited for pro
        "enterprise": 999999
    }

    # Admin users have unlimited access
    if current_user.is_admin:
        limit = 999999
        remaining = 999999
        can_create = True
    else:
        limit = PLAN_LIMITS.get(current_user.plan, 10)
        remaining = max(0, limit - current_user.matches_used)
        can_create = remaining > 0

    return UsageResponse(
        plan=current_user.plan,
        matches_used=current_user.matches_used,
        matches_limit=limit,
        matches_remaining=remaining,
        can_create_match=can_create
    )


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset email.
    Sends an email with a password reset token.
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()

    # Always return success to prevent email enumeration
    # (Don't reveal whether email exists in database)
    if not user:
        return {
            "message": "If that email address is in our system, we have sent a password reset link to it."
        }

    # Create password reset token (expires in 1 hour)
    reset_token_data = {
        "sub": user.email,
        "type": "password_reset",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    reset_token = jwt.encode(
        reset_token_data,
        settings.secret_key,
        algorithm=settings.algorithm
    )

    # Send password reset email
    frontend_url = settings.frontend_url or "http://localhost:3000"

    try:
        email_sent = email_service.send_password_reset_email(
            to_email=user.email,
            reset_token=reset_token,
            frontend_url=frontend_url
        )

        if not email_sent:
            # In development mode without SMTP, log the token
            from app.core.logging_config import get_logger
            logger = get_logger(__name__)
            logger.info(
                "Password reset token (SMTP not configured)",
                email=user.email,
                token=reset_token
            )

    except Exception as e:
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.error("Failed to send password reset email", error=str(e))
        # Continue anyway to not reveal if email exists

    return {
        "message": "If that email address is in our system, we have sent a password reset link to it."
    }


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using a valid reset token.
    """
    try:
        # Verify and decode token
        payload = jwt.decode(
            request.token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )

        email = payload.get("sub")
        token_type = payload.get("type")

        if not email or token_type != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

        # Find user
        user = db.query(User).filter(User.email == email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )

        # Update password
        user.hashed_password = get_password_hash(request.new_password)
        db.commit()

        return {
            "message": "Password has been reset successfully. You can now login with your new password."
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )


class GoogleAuthRequest(BaseModel):
    code: str


class GoogleAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/google", response_model=GoogleAuthResponse)
async def google_auth(
    request: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate or register user with Google OAuth.

    Args:
        request: Contains authorization code from Google OAuth callback

    Returns:
        JWT access token
    """
    code = request.code
    # Check if Google OAuth is configured
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured on the server"
        )

    try:
        # Initialize OAuth service
        oauth_service = OAuthService(
            google_client_id=settings.google_client_id,
            google_client_secret=settings.google_client_secret,
            redirect_uri=settings.google_redirect_uri
        )

        # Authenticate with Google
        user_data = await oauth_service.authenticate_with_google(code)

        if not user_data.get("email_verified"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not verified with Google"
            )

        email = user_data["email"]
        google_id = user_data["google_id"]

        # Check if user exists by email or Google ID
        user = db.query(User).filter(
            (User.email == email) | (User.google_id == google_id)
        ).first()

        if user:
            # Existing user - link Google ID if not already linked
            if not user.google_id:
                user.google_id = google_id
                db.commit()
                db.refresh(user)

        else:
            # New user - create account
            user = User(
                email=email,
                google_id=google_id,
                hashed_password=None,  # OAuth users don't have password
                api_key=generate_api_key(),
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Generate JWT access token
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )

        return GoogleAuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.error("Database error during Google OAuth", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Our authentication service is temporarily unavailable. Please try again in a moment."
        )
    except Exception as e:
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.error("Google OAuth failed", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed. Please try again or contact support if the problem persists."
        )


@router.post("/pro-interest")
async def express_pro_interest(
    request: ProPlanInterestRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Express interest in upgrading to Pro plan.
    Logs the interest for future notification when Pro launches.
    """
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)

    logger.info(
        "Pro plan interest expressed",
        user_id=current_user.id,
        email=request.email,
        feature=request.feature_interested_in
    )

    return {
        "message": "Thank you for your interest! We'll notify you when Pro features are available.",
        "status": "registered"
    }


@router.post("/contact-sales")
async def contact_sales(
    request: ContactSalesRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Contact sales for Enterprise plan.
    Logs the request and notifies the admin.
    """
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)

    logger.info(
        "Enterprise sales contact request",
        user_id=current_user.id,
        email=request.email,
        plan=request.plan,
        message=request.message
    )

    # You can add email notification to your sales team here
    # For now, just log it

    return {
        "message": "Thank you for your interest! Someone from our team will contact you shortly."
    }


@router.post("/feedback")
async def submit_feedback(request: UserFeedbackRequest):
    """
    Submit user feedback.
    Sends feedback to admin email via Brevo.
    This endpoint is public (no authentication required) for landing page feedback.
    """
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)

    # Get admin email from environment variable or use default
    admin_email = settings.admin_email if hasattr(settings, 'admin_email') else "saif.rehman2498@gmail.com"

    logger.info(
        "User feedback submitted",
        user_email=request.email,
        user_name=request.name
    )

    try:
        # Send feedback email
        success = email_service.send_feedback_email(
            user_email=request.email,
            user_name=request.name,
            feedback_message=request.message,
            admin_email=admin_email
        )

        if success:
            return {
                "message": "Thank you for your feedback! We'll get back to you soon."
            }
        else:
            logger.warning("Feedback email not sent (Brevo may not be configured)")
            return {
                "message": "Feedback received and logged. Thank you!"
            }

    except Exception as e:
        logger.error("Failed to process feedback", error=str(e))
        # Still return success to user, feedback is logged
        return {
            "message": "Feedback received and logged. Thank you!"
        }


@router.get("/pricing")
async def get_pricing():
    """
    Get pricing information and plan details.
    """
    return {
        "plans": [
            {
                "name": "Free",
                "price": 0,
                "features": [
                    "10 job matches",
                    "3 cover letters",
                    "3 interview preps",
                    "Basic resume parsing"
                ],
                "limits": {
                    "matches": 10,
                    "cover_letters": 3,
                    "interview_preps": 3
                }
            },
            {
                "name": "Pro",
                "price": "Coming Soon",
                "features": [
                    "Unlimited job matches",
                    "Unlimited cover letters",
                    "Unlimited interview preps",
                    "Advanced resume optimization",
                    "Priority support",
                    "Custom LLM preferences"
                ],
                "limits": {
                    "matches": "unlimited",
                    "cover_letters": "unlimited",
                    "interview_preps": "unlimited"
                },
                "available": False
            }
        ],
        "message": "Pro plan coming soon! Express your interest to get notified."
    }


@router.post("/tour/complete")
async def complete_tour(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark the onboarding tour as completed for the current user.
    Called when user finishes the guided walkthrough.
    """
    current_user.tour_completed = True
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Tour marked as completed",
        "tour_completed": True
    }
