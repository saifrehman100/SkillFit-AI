"""
Resume-Job matching endpoints.
"""
from typing import List, Optional
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.schemas import MatchRequest, BatchMatchRequest, MatchResponse
from app.core.auth import get_current_user, get_user_llm_api_key, create_smart_llm_client
from app.core.config import settings
from app.core.llm_providers import LLMFactory
from app.models.database import get_db
from app.models.models import User, Resume, Job, Match, APIUsage
from app.services.job_matcher import JobMatcher
from app.services.interview_generator import InterviewGenerator
from app.services.cover_letter_generator import CoverLetterGenerator
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Schemas for interview prep and cover letter
class InterviewPrepResponse(BaseModel):
    technical_questions: List[dict]
    behavioral_questions: List[dict]
    gap_questions: List[dict]
    talking_points: List[str]


class CoverLetterRequest(BaseModel):
    tone: Optional[str] = "professional"


class CoverLetterResponse(BaseModel):
    cover_letter: str
    candidate_name: str
    company: str
    job_title: str


@router.post("/", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
    match_request: MatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a match between a resume and job description.
    Returns match score, missing skills, and recommendations.
    """
    # Check usage limits for free tier
    PLAN_LIMITS = {
        "free": 10,
        "pro": 999999,
        "enterprise": 999999
    }

    limit = PLAN_LIMITS.get(current_user.plan, 10)
    # Admin users bypass usage limits
    if not current_user.is_admin and current_user.matches_used >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Free tier limit reached ({limit} matches). Please upgrade to Pro for unlimited matches."
        )

    # Verify resume ownership
    resume = db.query(Resume).filter(
        Resume.id == match_request.resume_id,
        Resume.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    # Verify job ownership
    job = db.query(Job).filter(
        Job.id == match_request.job_id,
        Job.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Get LLM client with smart routing
    # Job matching/ATS scoring is a SIMPLE task -> uses nano for OpenAI (cheaper)
    # If user specified a specific provider/model in request, respect that
    if match_request.llm_provider or match_request.llm_model:
        # User has specific preference in request - use it directly
        provider = match_request.llm_provider or current_user.llm_provider or settings.default_llm_provider
        model = match_request.llm_model or current_user.llm_model or settings.default_model_name
        api_key = get_user_llm_api_key(current_user, provider)

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No API key configured for provider: {provider}"
            )

        llm_client = LLMFactory.create_client(
            provider=provider,
            api_key=api_key,
            model=model
        )
    else:
        # Use smart routing - matching is a simple task
        llm_client = create_smart_llm_client(current_user, "simple")

    try:
        # Perform matching using nano (simple task: scoring, extraction)
        matcher = JobMatcher(llm_client)
        job_text = f"{job.description}\n\n{job.requirements or ''}"

        match_result = await matcher.match(
            resume_text=resume.raw_text,
            job_description=job_text,
            detailed=match_request.detailed
        )

        # Create match record
        match = Match(
            user_id=current_user.id,
            resume_id=resume.id,
            job_id=job.id,
            match_score=match_result.get("match_score", 0),
            missing_skills=match_result.get("missing_skills"),
            recommendations=match_result.get("recommendations"),
            explanation=match_result.get("explanation"),
            ats_score=match_result.get("ats_score"),
            keyword_matches=match_result.get("keyword_matches"),
            ats_issues=match_result.get("ats_issues"),
            llm_provider=match_result["_metadata"]["provider"],
            llm_model=match_result["_metadata"]["model"],
            tokens_used=match_result["_metadata"]["tokens_used"],
            cost_estimate=match_result["_metadata"]["cost_estimate"]
        )

        db.add(match)

        # Increment user's match usage counter
        current_user.matches_used += 1

        # Track API usage
        if settings.enable_cost_tracking:
            usage = APIUsage(
                user_id=current_user.id,
                endpoint="/api/v1/matches",
                llm_provider=match.llm_provider,
                llm_model=match.llm_model,
                tokens_used=match.tokens_used,
                cost_estimate=match.cost_estimate
            )
            db.add(usage)

        db.commit()
        db.refresh(match)

        # Track analytics event
        from app.models.models import Analytics
        analytics_event = Analytics(
            user_id=current_user.id,
            event_type="match_created",
            event_data={
                "match_id": match.id,
                "resume_id": resume.id,
                "job_id": job.id,
                "match_score": match.match_score
            }
        )
        db.add(analytics_event)
        db.commit()

        logger.info(
            "Match created",
            resume_id=resume.id,
            job_id=job.id,
            score=match.match_score
        )

        return match

    except Exception as e:
        logger.error("Match creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching failed: {str(e)}"
        )


@router.post("/batch", response_model=List[MatchResponse])
async def create_batch_matches(
    batch_request: BatchMatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create matches for multiple resumes against a single job.
    Useful for screening candidates.
    """
    # Check usage limits for free tier (batch counts as number of resumes)
    PLAN_LIMITS = {
        "free": 10,
        "pro": 999999,
        "enterprise": 999999
    }

    limit = PLAN_LIMITS.get(current_user.plan, 10)
    matches_to_create = len(batch_request.resume_ids)
    # Admin users bypass usage limits
    if not current_user.is_admin and current_user.matches_used + matches_to_create > limit:
        remaining = max(0, limit - current_user.matches_used)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Free tier limit would be exceeded. You have {remaining} matches remaining. Please upgrade to Pro for unlimited matches."
        )

    # Verify job ownership
    job = db.query(Job).filter(
        Job.id == batch_request.job_id,
        Job.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Verify all resumes exist and belong to user
    resumes = db.query(Resume).filter(
        Resume.id.in_(batch_request.resume_ids),
        Resume.user_id == current_user.id
    ).all()

    if len(resumes) != len(batch_request.resume_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more resumes not found"
        )

    # Get LLM client - Priority: request > user preference > system default
    provider = (
        batch_request.llm_provider or
        current_user.llm_provider or
        settings.default_llm_provider
    )
    model = (
        batch_request.llm_model or
        current_user.llm_model or
        settings.default_model_name
    )
    api_key = get_user_llm_api_key(current_user, provider)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No API key configured for provider: {provider}"
        )

    try:
        llm_client = LLMFactory.create_client(
            provider=provider,
            api_key=api_key,
            model=model
        )

        matcher = JobMatcher(llm_client)
        job_text = f"{job.description}\n\n{job.requirements or ''}"

        # Batch match
        resume_texts = [r.raw_text for r in resumes]
        match_results = await matcher.batch_match(
            resume_texts=resume_texts,
            job_description=job_text,
            detailed=batch_request.detailed
        )

        # Create match records
        matches = []
        for resume, result in zip(resumes, match_results):
            if "error" in result:
                logger.warning(f"Match failed for resume {resume.id}", error=result["error"])
                continue

            match = Match(
                user_id=current_user.id,
                resume_id=resume.id,
                job_id=job.id,
                match_score=result.get("match_score", 0),
                missing_skills=result.get("missing_skills"),
                recommendations=result.get("recommendations"),
                explanation=result.get("explanation"),
                llm_provider=result["_metadata"]["provider"],
                llm_model=result["_metadata"]["model"],
                tokens_used=result["_metadata"]["tokens_used"],
                cost_estimate=result["_metadata"]["cost_estimate"]
            )

            db.add(match)
            matches.append(match)

            # Track API usage
            if settings.enable_cost_tracking:
                usage = APIUsage(
                    user_id=current_user.id,
                    endpoint="/api/v1/matches/batch",
                    llm_provider=match.llm_provider,
                    llm_model=match.llm_model,
                    tokens_used=match.tokens_used,
                    cost_estimate=match.cost_estimate
                )
                db.add(usage)

        # Increment user's match usage counter by number of successful matches
        current_user.matches_used += len(matches)

        db.commit()

        for match in matches:
            db.refresh(match)

        logger.info(
            "Batch matches created",
            job_id=job.id,
            num_matches=len(matches)
        )

        return matches

    except Exception as e:
        logger.error("Batch matching failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch matching failed: {str(e)}"
        )


@router.get("/", response_model=List[MatchResponse])
async def list_matches(
    resume_id: int = None,
    job_id: int = None,
    min_score: float = 0,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all matches for the current user.
    Can filter by resume_id, job_id, or minimum score.
    """
    query = db.query(Match).filter(Match.user_id == current_user.id)

    if resume_id:
        query = query.filter(Match.resume_id == resume_id)

    if job_id:
        query = query.filter(Match.job_id == job_id)

    if min_score > 0:
        query = query.filter(Match.match_score >= min_score)

    matches = query.order_by(Match.created_at.desc()).offset(skip).limit(limit).all()

    return matches


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific match by ID.
    """
    match = db.query(Match).filter(
        Match.id == match_id,
        Match.user_id == current_user.id
    ).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    return match


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_match(
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a match.
    """
    match = db.query(Match).filter(
        Match.id == match_id,
        Match.user_id == current_user.id
    ).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    db.delete(match)
    db.commit()

    return None


@router.post("/{match_id}/interview-prep", response_model=InterviewPrepResponse)
async def generate_interview_prep(
    match_id: int,
    regenerate: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate interview preparation questions based on the match.
    Returns cached data if available unless regenerate=true.
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

    # Return cached data if available and not regenerating
    if match.interview_prep_data and not regenerate:
        logger.info("Returning cached interview prep", match_id=match_id)
        return match.interview_prep_data

    # Check usage limits for free tier (only when generating new content)
    INTERVIEW_PREP_LIMITS = {
        "free": 3,
        "pro": 999999,
        "enterprise": 999999
    }

    limit = INTERVIEW_PREP_LIMITS.get(current_user.plan, 3)
    # Admin users bypass usage limits
    if not current_user.is_admin and current_user.interview_preps_used >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Free tier limit reached ({limit} interview preps). Please upgrade to Pro for unlimited access."
        )

    # Get resume and job
    resume = db.query(Resume).filter(Resume.id == match.resume_id).first()
    job = db.query(Job).filter(Job.id == match.job_id).first()

    if not resume or not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume or job not found"
        )

    # Get LLM client
    provider = current_user.llm_provider or settings.default_llm_provider
    model = current_user.llm_model or settings.default_model_name
    api_key = get_user_llm_api_key(current_user, provider)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No API key configured for provider: {provider}"
        )

    try:
        llm_client = LLMFactory.create_client(
            provider=provider,
            api_key=api_key,
            model=model
        )

        # Generate interview prep
        generator = InterviewGenerator(llm_client)
        result = await generator.generate_questions(
            resume_text=resume.raw_text,
            job_description=f"{job.description}\n\n{job.requirements or ''}",
            job_title=job.title,
            company=job.company or "the company"
        )

        # Cache the result
        match.interview_prep_data = result

        # Increment usage counter
        current_user.interview_preps_used += 1

        db.commit()

        logger.info(
            "Interview prep generated and cached",
            match_id=match_id,
            usage=current_user.interview_preps_used
        )

        return result

    except Exception as e:
        logger.error("Interview prep generation failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate interview preparation. Please try again."
        )


@router.post("/{match_id}/cover-letter", response_model=CoverLetterResponse)
async def generate_cover_letter(
    match_id: int,
    request: CoverLetterRequest,
    regenerate: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a cover letter based on the match.
    Returns cached data if available unless regenerate=true or tone has changed.
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

    # Check if we have cached data with the same tone
    if match.cover_letter_data and not regenerate:
        cached_tone = match.cover_letter_data.get("tone", "professional")
        if cached_tone == request.tone:
            logger.info("Returning cached cover letter", match_id=match_id)
            return match.cover_letter_data

    # Check usage limits for free tier (only when generating new content)
    COVER_LETTER_LIMITS = {
        "free": 3,
        "pro": 999999,
        "enterprise": 999999
    }

    limit = COVER_LETTER_LIMITS.get(current_user.plan, 3)
    # Admin users bypass usage limits
    if not current_user.is_admin and current_user.cover_letters_used >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Free tier limit reached ({limit} cover letters). Please upgrade to Pro for unlimited access."
        )

    # Get resume and job
    resume = db.query(Resume).filter(Resume.id == match.resume_id).first()
    job = db.query(Job).filter(Job.id == match.job_id).first()

    if not resume or not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume or job not found"
        )

    # Get LLM client
    provider = current_user.llm_provider or settings.default_llm_provider
    model = current_user.llm_model or settings.default_model_name
    api_key = get_user_llm_api_key(current_user, provider)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No API key configured for provider: {provider}"
        )

    try:
        llm_client = LLMFactory.create_client(
            provider=provider,
            api_key=api_key,
            model=model
        )

        # Generate cover letter
        generator = CoverLetterGenerator(llm_client)
        result = await generator.generate(
            resume_text=resume.raw_text,
            job_title=job.title,
            company=job.company or "the company",
            job_description=f"{job.description}\n\n{job.requirements or ''}",
            tone=request.tone
        )

        # Add tone to result for caching
        result["tone"] = request.tone

        # Cache the result
        match.cover_letter_data = result

        # Increment usage counter
        current_user.cover_letters_used += 1

        db.commit()

        logger.info(
            "Cover letter generated and cached",
            match_id=match_id,
            tone=request.tone,
            usage=current_user.cover_letters_used
        )

        return result

    except Exception as e:
        logger.error("Cover letter generation failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cover letter. Please try again."
        )


@router.get("/{match_id}/cover-letter/download")
async def download_cover_letter(
    match_id: int,
    format: str = Query("pdf", regex="^(pdf|docx)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download the generated cover letter as PDF or DOCX.
    Requires cover letter to be generated first.
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

    if not match.cover_letter_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cover letter not generated yet. Generate it first."
        )

    # Get resume for contact info
    resume = db.query(Resume).filter(Resume.id == match.resume_id).first()
    job = db.query(Job).filter(Job.id == match.job_id).first()

    try:
        cover_letter_text = match.cover_letter_data.get("cover_letter", "")
        candidate_name = match.cover_letter_data.get("candidate_name", "Candidate")
        company = match.cover_letter_data.get("company", job.company if job else "Company")
        job_title = match.cover_letter_data.get("job_title", job.title if job else "Position")

        # Extract email from resume if available
        candidate_email = current_user.email

        if format == "pdf":
            file_stream = CoverLetterGenerator.create_pdf(
                cover_letter_text=cover_letter_text,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                company=company,
                job_title=job_title
            )
            media_type = "application/pdf"
            filename = f"cover_letter_{job_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        else:  # docx
            file_stream = CoverLetterGenerator.create_docx(
                cover_letter_text=cover_letter_text,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                company=company,
                job_title=job_title
            )
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"cover_letter_{job_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.docx"

        return StreamingResponse(
            file_stream,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error("Cover letter download failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cover letter document. Please try again."
        )


@router.get("/{match_id}/interview-prep/download")
async def download_interview_prep(
    match_id: int,
    format: str = Query("pdf", regex="^(pdf|docx)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download the generated interview prep as PDF or DOCX.
    Requires interview prep to be generated first.
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

    if not match.interview_prep_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview prep not generated yet. Generate it first."
        )

    # Get job info
    job = db.query(Job).filter(Job.id == match.job_id).first()

    try:
        job_title = job.title if job else "Position"
        company = job.company if job else "Company"

        if format == "pdf":
            file_stream = InterviewGenerator.create_pdf(
                interview_data=match.interview_prep_data,
                job_title=job_title,
                company=company
            )
            media_type = "application/pdf"
            filename = f"interview_prep_{job_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        else:  # docx
            file_stream = InterviewGenerator.create_docx(
                interview_data=match.interview_prep_data,
                job_title=job_title,
                company=company
            )
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"interview_prep_{job_title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.docx"

        return StreamingResponse(
            file_stream,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error("Interview prep download failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate interview prep document. Please try again."
        )

