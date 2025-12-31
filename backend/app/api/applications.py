"""
Application tracking endpoints for job applications.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.core.auth import get_current_user
from app.models.database import get_db
from app.models.models import User, Application, Job, Match

router = APIRouter()


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    app_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new job application tracking entry.
    """
    # Validate job_id if provided
    if app_data.job_id:
        job = db.query(Job).filter(
            Job.id == app_data.job_id,
            Job.user_id == current_user.id
        ).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

    # Validate match_id if provided
    if app_data.match_id:
        match = db.query(Match).filter(
            Match.id == app_data.match_id,
            Match.user_id == current_user.id
        ).first()
        if not match:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Match not found"
            )

    # Create application
    application = Application(
        user_id=current_user.id,
        job_id=app_data.job_id,
        match_id=app_data.match_id,
        company=app_data.company,
        position=app_data.position,
        status=app_data.status,
        application_date=app_data.application_date,
        job_url=app_data.job_url,
        notes=app_data.notes
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return application


@router.get("/", response_model=List[ApplicationResponse])
async def list_applications(
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all job applications for the current user.
    Optionally filter by status.
    """
    query = db.query(Application).filter(Application.user_id == current_user.id)

    if status_filter:
        # Validate status
        valid_statuses = ["wishlist", "applied", "interview", "offer", "rejected"]
        if status_filter not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        query = query.filter(Application.status == status_filter)

    # Order by created_at descending (most recent first)
    applications = query.order_by(Application.created_at.desc()).offset(skip).limit(limit).all()

    return applications


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific application by ID.
    """
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    return application


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    app_data: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an application (mainly for status changes).
    """
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    # Update fields (only update provided fields)
    if app_data.status is not None:
        application.status = app_data.status
    if app_data.application_date is not None:
        application.application_date = app_data.application_date
    if app_data.job_url is not None:
        application.job_url = app_data.job_url
    if app_data.notes is not None:
        application.notes = app_data.notes

    db.commit()
    db.refresh(application)

    return application


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an application.
    """
    application = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    db.delete(application)
    db.commit()

    return None
