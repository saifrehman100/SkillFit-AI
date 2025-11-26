"""
Resume-Job matching endpoints.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import MatchRequest, BatchMatchRequest, MatchResponse
from app.core.auth import get_current_user, get_user_llm_api_key
from app.core.config import settings
from app.core.llm_providers import LLMFactory
from app.models.database import get_db
from app.models.models import User, Resume, Job, Match, APIUsage
from app.services.job_matcher import JobMatcher
from app.core.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


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

    # Get LLM client
    provider = match_request.llm_provider or settings.default_llm_provider
    model = match_request.llm_model or settings.default_model_name
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

        # Perform matching
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
            llm_provider=match_result["_metadata"]["provider"],
            llm_model=match_result["_metadata"]["model"],
            tokens_used=match_result["_metadata"]["tokens_used"],
            cost_estimate=match_result["_metadata"]["cost_estimate"]
        )

        db.add(match)

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

    # Get LLM client
    provider = batch_request.llm_provider or settings.default_llm_provider
    model = batch_request.llm_model or settings.default_model_name
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

    matches = query.order_by(Match.match_score.desc()).offset(skip).limit(limit).all()

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
