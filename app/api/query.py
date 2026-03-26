from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import Optional

from app.db.session import SessionLocal
from app.models.user import User
from app.models.query_history import QueryHistory
from app.schemas.models import QueryHistoryResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/query-history", tags=["query-history"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[QueryHistoryResponse])
def get_user_query_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    platform: Optional[str] = Query(None, regex="^(amazon|aliexpress)$"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Get current user's query history.
    
    Query Parameters:
    - platform: Filter by "amazon" or "aliexpress" (optional)
    - limit: Number of results (1-500, default 50)
    - offset: Pagination offset (default 0)
    """
    query = select(QueryHistory).where(
        QueryHistory.user_id == current_user.id
    )

    # Optional platform filter
    if platform:
        query = query.where(QueryHistory.platform == platform)

    # Order by most recent first, then apply pagination
    query = query.order_by(desc(QueryHistory.created_at)).limit(limit).offset(offset)

    results = db.execute(query).scalars().all()

    return [
        QueryHistoryResponse(
            id=qh.id,
            user_id=qh.user_id,
            query_text=qh.query_text,
            platform=qh.platform,
            query_type=qh.query_type,
            s3_result_key=qh.s3_result_key,
            result_cached_at=qh.result_cached_at,
            total_products_returned=qh.total_products_returned,
            num_clusters=qh.num_clusters,
            created_at=qh.created_at,
            updated_at=qh.updated_at,
        )
        for qh in results
    ]


@router.get("/{query_id}", response_model=QueryHistoryResponse)
def get_query_history_by_id(
    query_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific query history by ID (must belong to current user)"""
    query_history = db.execute(
        select(QueryHistory).where(
            QueryHistory.id == query_id,
            QueryHistory.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if not query_history:
        raise HTTPException(status_code=404, detail="Query history not found")

    return QueryHistoryResponse(
        id=query_history.id,
        user_id=query_history.user_id,
        query_text=query_history.query_text,
        platform=query_history.platform,
        query_type=query_history.query_type,
        s3_result_key=query_history.s3_result_key,
        result_cached_at=query_history.result_cached_at,
        total_products_returned=query_history.total_products_returned,
        num_clusters=query_history.num_clusters,
        created_at=query_history.created_at,
        updated_at=query_history.updated_at,
    )
