"""
Resume management endpoints.
"""
import hashlib
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.schemas import ResumeResponse, ResumeUpload
from app.core.auth import get_current_user, get_user_llm_api_key
from app.core.config import settings
from app.core.llm_providers import LLMFactory
from app.models.database import get_db
from app.models.models import User, Resume
from app.services.resume_parser import ResumeParser, ResumeAnalyzer, ResumeParseError

router = APIRouter()


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    analyze: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and parse a resume.
    Optionally analyze it with LLM.
    """
    # Validate file size
    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.max_upload_size_mb}MB"
        )

    # Validate file extension
    file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_extension not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(settings.allowed_extensions)}"
        )

    # Parse resume
    try:
        text = ResumeParser.parse(content, file.filename)
    except ResumeParseError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Calculate hash for deduplication
    file_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicate
    existing = db.query(Resume).filter(
        Resume.user_id == current_user.id,
        Resume.upload_hash == file_hash
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This resume has already been uploaded"
        )

    # Create resume record
    resume = Resume(
        user_id=current_user.id,
        filename=file.filename,
        file_type=file_extension,
        raw_text=text,
        file_size=len(content),
        upload_hash=file_hash
    )

    # Analyze with LLM if requested
    if analyze:
        try:
            api_key = get_user_llm_api_key(current_user, settings.default_llm_provider)
            llm_client = LLMFactory.create_client(
                provider=settings.default_llm_provider,
                api_key=api_key,
                model=settings.default_model_name
            )

            analyzer = ResumeAnalyzer(llm_client)
            analysis = await analyzer.analyze(text)
            resume.parsed_data = analysis

        except Exception as e:
            # Continue without analysis if it fails
            resume.parsed_data = {"analysis_error": str(e)}

    db.add(resume)
    db.commit()
    db.refresh(resume)

    return resume


@router.get("/", response_model=List[ResumeResponse])
async def list_resumes(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all resumes for the current user.
    """
    resumes = db.query(Resume).filter(
        Resume.user_id == current_user.id
    ).offset(skip).limit(limit).all()

    return resumes


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific resume by ID.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a resume.
    """
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    db.delete(resume)
    db.commit()

    return None
