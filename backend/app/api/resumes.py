"""
Resume management endpoints.
"""
import hashlib
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.schemas import ResumeResponse, ResumeUpload
from app.core.auth import get_current_user, get_user_llm_api_key
from app.core.config import settings
from app.core.llm_providers import LLMFactory
from app.core.storage import get_storage_client
from app.models.database import get_db
from app.models.models import User, Resume, Job, Match
from app.services.resume_parser import ResumeParser, ResumeAnalyzer, ResumeParseError
from app.services.resume_rewriter import ResumeRewriter

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

    # Upload file to cloud storage
    storage = get_storage_client()
    content_type_map = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain"
    }
    content_type = content_type_map.get(file_extension, "application/octet-stream")

    try:
        file_path = storage.upload_file(
            file_content=content,
            filename=file.filename,
            content_type=content_type,
            user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage: {str(e)}"
        )

    # Create resume record
    resume = Resume(
        user_id=current_user.id,
        filename=file.filename,
        file_type=file_extension,
        raw_text=text,
        file_size=len(content),
        upload_hash=file_hash,
        file_path=file_path
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

    # Delete file from cloud storage if path exists
    if resume.file_path:
        storage = get_storage_client()
        try:
            storage.delete_file(resume.file_path)
        except Exception as e:
            # Log error but continue with database deletion
            print(f"Warning: Failed to delete file from storage: {str(e)}")

    db.delete(resume)
    db.commit()

    return None


@router.post("/{resume_id}/rewrite")
async def rewrite_resume(
    resume_id: int,
    job_id: int,
    match_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an improved version of a resume based on match recommendations.
    Requires a job ID to tailor the resume to.
    """
    # Get resume
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    # Get job
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Get match if provided, or find the most recent one
    if match_id:
        match = db.query(Match).filter(
            Match.id == match_id,
            Match.user_id == current_user.id
        ).first()
    else:
        match = db.query(Match).filter(
            Match.resume_id == resume_id,
            Match.job_id == job_id,
            Match.user_id == current_user.id
        ).order_by(Match.created_at.desc()).first()

    # Get match data if available
    match_score = match.match_score if match else 50
    recommendations = match.recommendations if match else []
    missing_skills = match.missing_skills if match else []

    try:
        # Get LLM client
        api_key = get_user_llm_api_key(current_user, settings.default_llm_provider)
        llm_client = LLMFactory.create_client(
            provider=settings.default_llm_provider,
            api_key=api_key,
            model=settings.default_model_name
        )

        # Rewrite resume
        rewriter = ResumeRewriter(llm_client)
        result = await rewriter.rewrite_resume(
            resume_text=resume.raw_text,
            job_description=job.description,
            match_score=match_score,
            recommendations=recommendations,
            missing_skills=missing_skills
        )

        return {
            "resume_id": resume_id,
            "job_id": job_id,
            "match_id": match.id if match else None,
            "original_score": match_score,
            **result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rewrite resume: {str(e)}"
        )
