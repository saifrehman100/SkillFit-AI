"""
Resume management endpoints.
"""
import hashlib
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Query
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
from app.services.resume_generator import ResumeGenerator
from app.services.interview_generator import InterviewGenerator
from app.services.cover_letter_generator import CoverLetterGenerator
from fastapi.responses import StreamingResponse
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Schema for improved resume download
class ImprovedResumeDownloadRequest(BaseModel):
    match_id: int
    format: str = "pdf"  # pdf or docx


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
    regenerate: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an improved version of a resume based on match recommendations.
    Requires a job ID to tailor the resume to.
    Returns cached data if available unless regenerate=true.
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

    # Return cached data if available and not regenerating
    if match and match.improved_resume_data and not regenerate:
        logger.info("Returning cached improved resume", match_id=match.id if match else None)
        return match.improved_resume_data

    # Check usage limits for free tier (only when generating new content)
    RESUME_REWRITE_LIMITS = {
        "free": 3,
        "pro": 999999,
        "enterprise": 999999
    }

    limit = RESUME_REWRITE_LIMITS.get(current_user.plan, 3)
    if current_user.resume_rewrites_used >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Free tier limit reached ({limit} resume rewrites). Please upgrade to Pro for unlimited access."
        )

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

        response_data = {
            "resume_id": resume_id,
            "job_id": job_id,
            "match_id": match.id if match else None,
            "original_score": match_score,
            **result
        }

        # Cache the result if we have a match
        if match:
            match.improved_resume_data = response_data

        # Increment usage counter
        current_user.resume_rewrites_used += 1

        db.commit()

        return response_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rewrite resume: {str(e)}"
        )


@router.get("/{resume_id}/download-docx")
async def download_resume_docx(
    resume_id: int,
    improved_text: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download resume as DOCX file.
    Can download original resume or improved version if improved_text is provided.
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

    try:
        # Use improved text if provided, otherwise use original
        resume_text = improved_text if improved_text else resume.raw_text

        # Generate DOCX
        generator = ResumeGenerator()
        docx_file = generator.create_professional_docx(
            resume_text=resume_text,
            candidate_name=None,  # Could extract from resume
            filename=f"{resume.filename.rsplit('.', 1)[0]}.docx"
        )

        # Return as downloadable file
        return StreamingResponse(
            docx_file,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={resume.filename.rsplit('.', 1)[0]}.docx"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate DOCX: {str(e)}"
        )


@router.get("/{resume_id}/download-pdf")
async def download_resume_pdf(
    resume_id: int,
    improved_text: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download resume as PDF file.
    Can download original resume or improved version if improved_text is provided.
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

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from io import BytesIO

        # Use improved text if provided, otherwise use original
        resume_text = improved_text if improved_text else resume.raw_text

        # Create PDF
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter,
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)

        styles = getSampleStyleSheet()
        story = []

        # Parse and add content
        lines = resume_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.2*inch))
                continue

            # Detect headers
            is_header = any(keyword in line.upper() for keyword in [
                'SUMMARY', 'EXPERIENCE', 'EDUCATION', 'SKILLS',
                'PROJECTS', 'CERTIFICATIONS'
            ])

            if is_header:
                p = Paragraph(line, styles['Heading2'])
            else:
                p = Paragraph(line, styles['Normal'])

            story.append(p)
            story.append(Spacer(1, 0.1*inch))

        doc.build(story)
        pdf_buffer.seek(0)

        # Return as downloadable file
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={resume.filename.rsplit('.', 1)[0]}.pdf"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )


@router.post("/{resume_id}/generate-interview")
async def generate_interview_questions(
    resume_id: int,
    job_id: int,
    match_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate interview preparation questions and talking points.
    Tailored to the resume and specific job posting.
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
    match = None
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
    match_score = match.match_score if match else None
    missing_skills = match.missing_skills if match else None
    recommendations = match.recommendations if match else None

    try:
        # Get LLM client
        api_key = get_user_llm_api_key(current_user, settings.default_llm_provider)
        llm_client = LLMFactory.create_client(
            provider=settings.default_llm_provider,
            api_key=api_key,
            model=settings.default_model_name
        )

        # Generate interview questions
        generator = InterviewGenerator(llm_client)
        result = await generator.generate_questions(
            resume_text=resume.raw_text,
            job_description=job.description,
            job_title=job.title,
            company=job.company or "the company",
            match_score=match_score,
            missing_skills=missing_skills,
            recommendations=recommendations
        )

        return {
            "resume_id": resume_id,
            "job_id": job_id,
            "match_id": match.id if match else None,
            "job_title": job.title,
            "company": job.company,
            **result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate interview questions: {str(e)}"
        )


@router.get("/{resume_id}/interview-prep-docx")
async def download_interview_prep_docx(
    resume_id: int,
    job_id: int,
    match_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download interview preparation guide as DOCX.
    Generates questions and talking points tailored to the resume and job.
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

    # Get match if available
    match = None
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

    match_score = match.match_score if match else None
    missing_skills = match.missing_skills if match else None
    recommendations = match.recommendations if match else None

    try:
        # Get LLM client
        api_key = get_user_llm_api_key(current_user, settings.default_llm_provider)
        llm_client = LLMFactory.create_client(
            provider=settings.default_llm_provider,
            api_key=api_key,
            model=settings.default_model_name
        )

        # Generate interview questions
        generator = InterviewGenerator(llm_client)
        interview_data = await generator.generate_questions(
            resume_text=resume.raw_text,
            job_description=job.description,
            job_title=job.title,
            company=job.company or "Company",
            match_score=match_score,
            missing_skills=missing_skills,
            recommendations=recommendations
        )

        # Create DOCX
        docx_file = InterviewGenerator.create_docx(
            interview_data=interview_data,
            job_title=job.title,
            company=job.company or "Company"
        )

        # Return as downloadable file
        filename = f"interview_prep_{job.title.replace(' ', '_')}.docx"
        return StreamingResponse(
            docx_file,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate interview prep DOCX: {str(e)}"
        )


@router.get("/{resume_id}/interview-prep-pdf")
async def download_interview_prep_pdf(
    resume_id: int,
    job_id: int,
    match_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download interview preparation guide as PDF.
    Generates questions and talking points tailored to the resume and job.
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

    # Get match if available
    match = None
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

    match_score = match.match_score if match else None
    missing_skills = match.missing_skills if match else None
    recommendations = match.recommendations if match else None

    try:
        # Get LLM client
        api_key = get_user_llm_api_key(current_user, settings.default_llm_provider)
        llm_client = LLMFactory.create_client(
            provider=settings.default_llm_provider,
            api_key=api_key,
            model=settings.default_model_name
        )

        # Generate interview questions
        generator = InterviewGenerator(llm_client)
        interview_data = await generator.generate_questions(
            resume_text=resume.raw_text,
            job_description=job.description,
            job_title=job.title,
            company=job.company or "Company",
            match_score=match_score,
            missing_skills=missing_skills,
            recommendations=recommendations
        )

        # Create PDF
        pdf_file = InterviewGenerator.create_pdf(
            interview_data=interview_data,
            job_title=job.title,
            company=job.company or "Company"
        )

        # Return as downloadable file
        filename = f"interview_prep_{job.title.replace(' ', '_')}.pdf"
        return StreamingResponse(
            pdf_file,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate interview prep PDF: {str(e)}"
        )


@router.post("/{resume_id}/generate-cover-letter")
async def generate_cover_letter(
    resume_id: int,
    job_id: int,
    tone: str = "professional",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a tailored cover letter for a specific job.

    Args:
        tone: One of 'professional', 'enthusiastic', or 'formal'
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

    try:
        # Get LLM client
        api_key = get_user_llm_api_key(current_user, settings.default_llm_provider)
        llm_client = LLMFactory.create_client(
            provider=settings.default_llm_provider,
            api_key=api_key,
            model=settings.default_model_name
        )

        # Generate cover letter
        generator = CoverLetterGenerator(llm_client)
        result = await generator.generate(
            resume_text=resume.raw_text,
            job_description=job.description,
            job_title=job.title,
            company=job.company or "the company",
            tone=tone
        )

        return {
            "resume_id": resume_id,
            "job_id": job_id,
            "job_title": job.title,
            "company": job.company,
            **result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cover letter: {str(e)}"
        )


@router.get("/{resume_id}/cover-letter-docx")
async def download_cover_letter_docx(
    resume_id: int,
    job_id: int,
    tone: str = "professional",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download cover letter as DOCX.
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

    try:
        # Get LLM client
        api_key = get_user_llm_api_key(current_user, settings.default_llm_provider)
        llm_client = LLMFactory.create_client(
            provider=settings.default_llm_provider,
            api_key=api_key,
            model=settings.default_model_name
        )

        # Generate cover letter
        generator = CoverLetterGenerator(llm_client)
        cover_letter_data = await generator.generate(
            resume_text=resume.raw_text,
            job_description=job.description,
            job_title=job.title,
            company=job.company or "Company",
            tone=tone
        )

        # Create DOCX
        docx_file = CoverLetterGenerator.create_docx(
            cover_letter_text=cover_letter_data["cover_letter"],
            candidate_name=cover_letter_data["candidate_name"],
            company=job.company or "Company",
            job_title=job.title
        )

        # Return as downloadable file
        filename = f"cover_letter_{job.company or 'Company'}_{job.title.replace(' ', '_')}.docx"
        return StreamingResponse(
            docx_file,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cover letter DOCX: {str(e)}"
        )


@router.get("/{resume_id}/cover-letter-pdf")
async def download_cover_letter_pdf(
    resume_id: int,
    job_id: int,
    tone: str = "professional",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download cover letter as PDF.
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

    try:
        # Get LLM client
        api_key = get_user_llm_api_key(current_user, settings.default_llm_provider)
        llm_client = LLMFactory.create_client(
            provider=settings.default_llm_provider,
            api_key=api_key,
            model=settings.default_model_name
        )

        # Generate cover letter
        generator = CoverLetterGenerator(llm_client)
        cover_letter_data = await generator.generate(
            resume_text=resume.raw_text,
            job_description=job.description,
            job_title=job.title,
            company=job.company or "Company",
            tone=tone
        )

        # Create PDF
        pdf_file = CoverLetterGenerator.create_pdf(
            cover_letter_text=cover_letter_data["cover_letter"],
            candidate_name=cover_letter_data["candidate_name"],
            company=job.company or "Company",
            job_title=job.title
        )

        # Return as downloadable file
        filename = f"cover_letter_{job.company or 'Company'}_{job.title.replace(' ', '_')}.pdf"
        return StreamingResponse(
            pdf_file,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate cover letter PDF: {str(e)}"
        )


@router.get("/improved/{match_id}/download")
async def download_improved_resume(
    match_id: int,
    format: str = Query("pdf", regex="^(pdf|docx)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download the improved resume from a match as PDF or DOCX.
    Requires the resume to have been rewritten first.
    """
    # Get match
    match = db.query(Match).filter(
        Match.id == match_id,
        Match.user_id == current_user.id
    ).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    if not match.improved_resume_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Improved resume not generated yet. Generate it first via /resumes/{id}/rewrite endpoint."
        )

    # Get the improved text
    improved_text = match.improved_resume_data.get("improved_resume", "")
    if not improved_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No improved resume text available"
        )

    # Get resume and job for metadata
    resume = db.query(Resume).filter(Resume.id == match.resume_id).first()
    job = db.query(Job).filter(Job.id == match.job_id).first()

    try:
        if format == "pdf":
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from io import BytesIO

            # Create PDF
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter,
                                    rightMargin=0.75*inch, leftMargin=0.75*inch,
                                    topMargin=0.75*inch, bottomMargin=0.75*inch)

            styles = getSampleStyleSheet()
            story = []

            # Parse and add content
            lines = improved_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 0.2*inch))
                    continue

                # Detect headers
                is_header = any(keyword in line.upper() for keyword in [
                    'SUMMARY', 'EXPERIENCE', 'EDUCATION', 'SKILLS',
                    'PROJECTS', 'CERTIFICATIONS'
                ])

                if is_header:
                    p = Paragraph(line, styles['Heading2'])
                else:
                    p = Paragraph(line, styles['Normal'])

                story.append(p)
                story.append(Spacer(1, 0.1*inch))

            doc.build(story)
            pdf_buffer.seek(0)

            filename = f"improved_resume_{job.title.replace(' ', '_') if job else 'optimized'}_{datetime.now().strftime('%Y%m%d')}.pdf"

            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:  # docx
            generator = ResumeGenerator()
            docx_file = generator.create_professional_docx(
                resume_text=improved_text,
                candidate_name=None,
                filename=f"improved_resume_{job.title.replace(' ', '_') if job else 'optimized'}.docx"
            )

            filename = f"improved_resume_{job.title.replace(' ', '_') if job else 'optimized'}_{datetime.now().strftime('%Y%m%d')}.docx"

            return StreamingResponse(
                docx_file,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

    except Exception as e:
        logger.error("Failed to download improved resume", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate improved resume document. Please try again."
        )


@router.post("/improved/{match_id}/save")
async def save_improved_resume(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save the improved resume from a match as a new resume in user's collection.
    This creates a new resume entry that can be used for future job matches.
    """
    # Get match
    match = db.query(Match).filter(
        Match.id == match_id,
        Match.user_id == current_user.id
    ).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    if not match.improved_resume_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Improved resume not generated yet. Generate it first via /resumes/{id}/rewrite endpoint."
        )

    # Get the improved text
    improved_text = match.improved_resume_data.get("improved_resume", "")
    if not improved_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No improved resume text available"
        )

    # Get original resume and job for metadata
    original_resume = db.query(Resume).filter(Resume.id == match.resume_id).first()
    job = db.query(Job).filter(Job.id == match.job_id).first()

    try:
        # Calculate hash for deduplication
        text_hash = hashlib.sha256(improved_text.encode()).hexdigest()

        # Check if this improved resume was already saved
        existing = db.query(Resume).filter(
            Resume.user_id == current_user.id,
            Resume.upload_hash == text_hash
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This improved resume has already been saved to your collection"
            )

        # Create new resume record
        new_filename = f"improved_{original_resume.filename.rsplit('.', 1)[0]}_{job.title.replace(' ', '_') if job else 'optimized'}.txt"

        new_resume = Resume(
            user_id=current_user.id,
            filename=new_filename,
            file_type="txt",
            raw_text=improved_text,
            file_size=len(improved_text.encode()),
            upload_hash=text_hash,
            file_path=None,  # Not uploaded to cloud storage
            parsed_data={
                "source": "improved_resume",
                "original_resume_id": original_resume.id,
                "job_id": job.id if job else None,
                "match_id": match_id,
                "improvements_applied": match.improved_resume_data.get("changes_made", [])
            }
        )

        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)

        logger.info(
            "Improved resume saved",
            new_resume_id=new_resume.id,
            match_id=match_id,
            user_id=current_user.id
        )

        return {
            "message": "Improved resume saved successfully!",
            "resume": ResumeResponse.from_orm(new_resume),
            "can_use_for_matching": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to save improved resume", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save improved resume. Please try again."
        )


@router.post("/improved/{match_id}/rescan")
async def rescan_improved_resume(
    match_id: int,
    save_to_collection: bool = Query(False, description="Automatically save to resume collection after scanning"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Rescan/reanalyze the improved resume with LLM.
    Optionally save it to the user's resume collection.

    This allows users to:
    1. See what the LLM thinks of the improved resume
    2. Get a fresh analysis with structured data
    3. Optionally save it for future job matches
    """
    # Get match
    match = db.query(Match).filter(
        Match.id == match_id,
        Match.user_id == current_user.id
    ).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    if not match.improved_resume_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Improved resume not generated yet. Generate it first via /resumes/{id}/rewrite endpoint."
        )

    # Check usage limits for free tier (rescanning counts toward match limit)
    PLAN_LIMITS = {
        "free": 10,
        "pro": 999999,
        "enterprise": 999999
    }

    limit = PLAN_LIMITS.get(current_user.plan, 10)
    if current_user.matches_used >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Free tier limit reached ({limit} matches). Rescanning counts toward your match limit. Please upgrade to Pro for unlimited access."
        )

    # Get the improved text
    improved_text = match.improved_resume_data.get("improved_resume", "")
    if not improved_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No improved resume text available"
        )

    try:
        # Analyze the improved resume
        api_key = get_user_llm_api_key(current_user, settings.default_llm_provider)
        llm_client = LLMFactory.create_client(
            provider=settings.default_llm_provider,
            api_key=api_key,
            model=settings.default_model_name
        )

        analyzer = ResumeAnalyzer(llm_client)
        analysis = await analyzer.analyze(improved_text)

        # Recalculate match scores with the improved resume
        job = db.query(Job).filter(Job.id == match.job_id).first()
        if job:
            from app.services.matcher import JobMatcher
            matcher = JobMatcher(llm_client)
            job_text = f"{job.description}\n\n{job.requirements or ''}"

            match_result = await matcher.match(
                resume_text=improved_text,
                job_description=job_text,
                detailed=True
            )

            # Update match scores with improved resume results
            match.match_score = match_result.get("match_score", match.match_score)
            match.ats_score = match_result.get("ats_score", match.ats_score)
            match.missing_skills = match_result.get("missing_skills", match.missing_skills)
            match.recommendations = match_result.get("recommendations", match.recommendations)
            match.explanation = match_result.get("explanation", match.explanation)
            match.keyword_matches = match_result.get("keyword_matches", match.keyword_matches)
            match.ats_issues = match_result.get("ats_issues", match.ats_issues)

            logger.info(
                "Match scores updated after rescan",
                match_id=match_id,
                new_match_score=match.match_score,
                new_ats_score=match.ats_score
            )

            # Commit the updated match scores
            db.commit()
            db.refresh(match)

        # Increment user's match usage counter (rescan counts as a match)
        current_user.matches_used += 1
        db.commit()

        # If user wants to save it, create a new resume
        saved_resume = None
        if save_to_collection:
            # Calculate hash for deduplication
            text_hash = hashlib.sha256(improved_text.encode()).hexdigest()

            # Check if already saved
            existing = db.query(Resume).filter(
                Resume.user_id == current_user.id,
                Resume.upload_hash == text_hash
            ).first()

            if not existing:
                # Get original resume and job for metadata
                original_resume = db.query(Resume).filter(Resume.id == match.resume_id).first()
                job = db.query(Job).filter(Job.id == match.job_id).first()

                new_filename = f"improved_{original_resume.filename.rsplit('.', 1)[0]}_{job.title.replace(' ', '_') if job else 'optimized'}.txt"

                new_resume = Resume(
                    user_id=current_user.id,
                    filename=new_filename,
                    file_type="txt",
                    raw_text=improved_text,
                    parsed_data=analysis,
                    file_size=len(improved_text.encode()),
                    upload_hash=text_hash,
                    file_path=None
                )

                db.add(new_resume)
                db.commit()
                db.refresh(new_resume)

                saved_resume = new_resume

                logger.info(
                    "Improved resume rescanned and saved",
                    new_resume_id=new_resume.id,
                    match_id=match_id
                )

        return {
            "analysis": analysis,
            "improved_text": improved_text,
            "saved": save_to_collection and saved_resume is not None,
            "saved_resume": ResumeResponse.from_orm(saved_resume) if saved_resume else None,
            "message": "Resume analyzed successfully!" + (" Saved to your collection." if saved_resume else "")
        }

    except Exception as e:
        logger.error("Failed to rescan improved resume", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze improved resume. Please try again."
        )
