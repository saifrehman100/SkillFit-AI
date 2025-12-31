"""
Job description management endpoints.
"""
import hashlib
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import JobCreate, JobResponse
from app.core.auth import get_current_user, get_user_llm_api_key
from app.core.config import settings
from app.core.llm_providers import LLMFactory
from app.models.database import get_db
from app.models.models import User, Job
from app.services.job_matcher import SkillExtractor
from app.services.job_scraper import JobScraper, JobScraperError

router = APIRouter()


@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    analyze: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new job description.
    Optionally extract skills with LLM.
    """
    # Calculate hash for deduplication
    content = f"{job_data.title}|{job_data.company}|{job_data.description}"
    job_hash = hashlib.sha256(content.encode()).hexdigest()

    # Check for duplicate
    existing = db.query(Job).filter(
        Job.user_id == current_user.id,
        Job.job_hash == job_hash
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This job description already exists"
        )

    # Create job record
    job = Job(
        user_id=current_user.id,
        title=job_data.title,
        company=job_data.company,
        description=job_data.description,
        requirements=job_data.requirements,
        source_url=job_data.source_url,
        job_hash=job_hash
    )

    # Extract skills with LLM if requested
    if analyze:
        try:
            api_key = get_user_llm_api_key(current_user, settings.default_llm_provider)
            llm_client = LLMFactory.create_client(
                provider=settings.default_llm_provider,
                api_key=api_key,
                model=settings.default_model_name
            )

            extractor = SkillExtractor(llm_client)
            full_description = f"{job_data.description}\n\n{job_data.requirements or ''}"
            skills_data = await extractor.extract_skills(full_description)
            job.parsed_data = skills_data

        except Exception as e:
            # Continue without analysis if it fails
            job.parsed_data = {"extraction_error": str(e)}

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@router.post("/import-from-url", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def import_job_from_url(
    url: str,
    analyze: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Import a job description from a URL (LinkedIn, Indeed, Glassdoor, etc.).
    Automatically extracts job details and creates a job record.
    """
    try:
        # Scrape job details from URL
        job_details = await JobScraper.scrape_job(url)

    except JobScraperError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import job: {str(e)}"
        )

    # Calculate hash for deduplication
    content = f"{job_details['title']}|{job_details['company']}|{job_details['description']}"
    job_hash = hashlib.sha256(content.encode()).hexdigest()

    # Check for duplicate
    existing = db.query(Job).filter(
        Job.user_id == current_user.id,
        Job.job_hash == job_hash
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This job description already exists"
        )

    # Create job record
    job = Job(
        user_id=current_user.id,
        title=job_details['title'],
        company=job_details['company'],
        description=job_details['description'],
        requirements=job_details.get('requirements'),
        source_url=job_details['source_url'],
        job_hash=job_hash
    )

    # Extract skills with LLM if requested
    if analyze:
        try:
            api_key = get_user_llm_api_key(current_user, settings.default_llm_provider)
            llm_client = LLMFactory.create_client(
                provider=settings.default_llm_provider,
                api_key=api_key,
                model=settings.default_model_name
            )

            extractor = SkillExtractor(llm_client)
            full_description = f"{job_details['description']}\n\n{job_details.get('requirements') or ''}"
            skills_data = await extractor.extract_skills(full_description)
            job.parsed_data = skills_data

        except Exception as e:
            # Continue without analysis if it fails
            job.parsed_data = {"extraction_error": str(e)}

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@router.get("/", response_model=List[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all job descriptions for the current user.
    """
    query = db.query(Job).filter(Job.user_id == current_user.id)

    if active_only:
        query = query.filter(Job.is_active == True)

    jobs = query.offset(skip).limit(limit).all()

    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific job description by ID.
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return job


@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a job description.
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    # Update fields
    job.title = job_data.title
    job.company = job_data.company
    job.description = job_data.description
    job.requirements = job_data.requirements
    job.source_url = job_data.source_url

    db.commit()
    db.refresh(job)

    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a job description.
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    db.delete(job)
    db.commit()

    return None
