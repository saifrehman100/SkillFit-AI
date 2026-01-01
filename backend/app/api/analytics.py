"""
Analytics endpoints for tracking and viewing usage statistics.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, cast, String

from app.core.auth import get_current_user, get_admin_user
from app.models.database import get_db
from app.models.models import User, Analytics
from pydantic import BaseModel

router = APIRouter()


class AnalyticsEvent(BaseModel):
    """Schema for tracking analytics events."""
    event_type: str
    event_data: Optional[dict] = None


class AnalyticsStats(BaseModel):
    """Schema for analytics statistics."""
    total_events: int
    events_by_type: dict
    daily_events: List[dict]
    top_pages: List[dict]


@router.post("/track")
async def track_event(
    event: AnalyticsEvent,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Track an analytics event.

    Events can be tracked for both authenticated and anonymous users.
    """
    # Create analytics record
    analytics_record = Analytics(
        user_id=current_user.id if current_user else None,
        event_type=event.event_type,
        event_data=event.event_data,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        referrer=request.headers.get("referer")
    )

    db.add(analytics_record)
    db.commit()

    return {"status": "tracked", "event_type": event.event_type}


@router.get("/stats", response_model=AnalyticsStats)
async def get_analytics_stats(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analytics statistics for the current user.

    Args:
        days: Number of days to look back (default: 30)
    """
    # Calculate date range
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get user's events
    user_events = db.query(Analytics).filter(
        and_(
            Analytics.user_id == current_user.id,
            Analytics.created_at >= start_date
        )
    ).all()

    # Total events
    total_events = len(user_events)

    # Events by type
    events_by_type = {}
    for event in user_events:
        event_type = event.event_type
        events_by_type[event_type] = events_by_type.get(event_type, 0) + 1

    # Daily events (last 30 days)
    daily_query = db.query(
        func.date(Analytics.created_at).label('date'),
        func.count(Analytics.id).label('count')
    ).filter(
        and_(
            Analytics.user_id == current_user.id,
            Analytics.created_at >= start_date
        )
    ).group_by(
        func.date(Analytics.created_at)
    ).order_by(
        func.date(Analytics.created_at)
    ).all()

    daily_events = [
        {"date": str(row.date), "count": row.count}
        for row in daily_query
    ]

    # Top pages (for page_view events)
    top_pages_query = db.query(
        cast(Analytics.event_data['page'], String).label('page'),
        func.count(Analytics.id).label('views')
    ).filter(
        and_(
            Analytics.user_id == current_user.id,
            Analytics.event_type == 'page_view',
            Analytics.created_at >= start_date
        )
    ).group_by(
        cast(Analytics.event_data['page'], String)
    ).order_by(
        func.count(Analytics.id).desc()
    ).limit(10).all()

    top_pages = [
        {"page": row.page, "views": row.views}
        for row in top_pages_query
        if row.page  # Filter out None values
    ]

    return AnalyticsStats(
        total_events=total_events,
        events_by_type=events_by_type,
        daily_events=daily_events,
        top_pages=top_pages
    )


@router.get("/admin/stats")
async def get_admin_analytics(
    days: int = 30,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get platform-wide analytics statistics.

    **Admin Only** - Requires is_admin=true in user record.
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    # Total users
    total_users = db.query(func.count(User.id)).scalar()

    # New users in period
    new_users = db.query(func.count(User.id)).filter(
        User.created_at >= start_date
    ).scalar()

    # Total events
    total_events = db.query(func.count(Analytics.id)).filter(
        Analytics.created_at >= start_date
    ).scalar()

    # Events by type
    events_by_type_query = db.query(
        Analytics.event_type,
        func.count(Analytics.id).label('count')
    ).filter(
        Analytics.created_at >= start_date
    ).group_by(
        Analytics.event_type
    ).order_by(
        func.count(Analytics.id).desc()
    ).all()

    events_by_type = {row.event_type: row.count for row in events_by_type_query}

    # Daily active users
    dau_query = db.query(
        func.date(Analytics.created_at).label('date'),
        func.count(func.distinct(Analytics.user_id)).label('active_users')
    ).filter(
        and_(
            Analytics.created_at >= start_date,
            Analytics.user_id.isnot(None)
        )
    ).group_by(
        func.date(Analytics.created_at)
    ).order_by(
        func.date(Analytics.created_at)
    ).all()

    daily_active_users = [
        {"date": str(row.date), "active_users": row.active_users}
        for row in dau_query
    ]

    return {
        "total_users": total_users,
        "new_users": new_users,
        "total_events": total_events,
        "events_by_type": events_by_type,
        "daily_active_users": daily_active_users
    }
