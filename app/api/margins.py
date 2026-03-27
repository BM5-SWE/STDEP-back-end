from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import Optional

from app.db.session import SessionLocal
from app.models.user import User
from app.models.margin_estimate import MarginEstimate
from app.schemas.models import MarginEstimateCreate, MarginEstimateUpdate, MarginEstimateResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/margin-estimates", tags=["margin-estimates"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def calculate_margins(cost_price: float, selling_price: Optional[float]) -> tuple[Optional[float], Optional[float]]:
    """
    Calculate estimated margin and margin percentage.
    
    Returns: (estimated_margin, margin_percentage) or (None, None) if selling_price not provided
    """
    if selling_price is None:
        return None, None
    
    estimated_margin = selling_price - cost_price
    margin_percentage = (estimated_margin / cost_price * 100) if cost_price > 0 else 0
    
    return estimated_margin, margin_percentage


@router.post("", response_model=MarginEstimateResponse, status_code=status.HTTP_201_CREATED)
def create_margin_estimate(
    estimate_data: MarginEstimateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new margin estimate.
    
    Request body:
    - product_name: str (required)
    - platform: str (required) - "amazon" or "aliexpress"
    - cost_price: float (required) - Cost of product
    - selling_price: float (optional) - Selling price
    - currency: str (optional) - Currency code (e.g., "USD")
    - saved_product_id: UUID (optional) - Link to saved product
    - notes: str (optional) - Additional notes
    
    Automatically calculates estimated_margin and margin_percentage if selling_price provided.
    """
    estimated_margin, margin_percentage = calculate_margins(
        estimate_data.cost_price,
        estimate_data.selling_price
    )

    new_estimate = MarginEstimate(
        user_id=current_user.id,
        product_name=estimate_data.product_name,
        platform=estimate_data.platform,
        cost_price=estimate_data.cost_price,
        selling_price=estimate_data.selling_price,
        currency=estimate_data.currency,
        saved_product_id=estimate_data.saved_product_id,
        notes=estimate_data.notes,
        estimated_margin=estimated_margin,
        margin_percentage=margin_percentage,
    )

    db.add(new_estimate)
    db.commit()
    db.refresh(new_estimate)

    return MarginEstimateResponse(
        id=new_estimate.id,
        user_id=new_estimate.user_id,
        saved_product_id=new_estimate.saved_product_id,
        product_name=new_estimate.product_name,
        platform=new_estimate.platform,
        cost_price=new_estimate.cost_price,
        selling_price=new_estimate.selling_price,
        currency=new_estimate.currency,
        estimated_margin=new_estimate.estimated_margin,
        margin_percentage=new_estimate.margin_percentage,
        notes=new_estimate.notes,
        created_at=new_estimate.created_at,
        updated_at=new_estimate.updated_at,
    )


@router.get("", response_model=list[MarginEstimateResponse])
def get_margin_estimates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    platform: Optional[str] = Query(None, regex="^(amazon|aliexpress)$"),
    min_margin: Optional[float] = Query(None, description="Filter by minimum margin percentage"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Get current user's margin estimates.
    
    Query Parameters:
    - platform: Filter by "amazon" or "aliexpress" (optional)
    - min_margin: Filter by minimum margin percentage (optional)
    - limit: Number of results (1-500, default 50)
    - offset: Pagination offset (default 0)
    """
    query = select(MarginEstimate).where(
        MarginEstimate.user_id == current_user.id
    )

    # Optional filters
    if platform:
        query = query.where(MarginEstimate.platform == platform)
    if min_margin is not None:
        query = query.where(MarginEstimate.margin_percentage >= min_margin)

    # Order by most recently created first, then apply pagination
    query = query.order_by(desc(MarginEstimate.created_at)).limit(limit).offset(offset)

    results = db.execute(query).scalars().all()

    return [
        MarginEstimateResponse(
            id=me.id,
            user_id=me.user_id,
            saved_product_id=me.saved_product_id,
            product_name=me.product_name,
            platform=me.platform,
            cost_price=me.cost_price,
            selling_price=me.selling_price,
            currency=me.currency,
            estimated_margin=me.estimated_margin,
            margin_percentage=me.margin_percentage,
            notes=me.notes,
            created_at=me.created_at,
            updated_at=me.updated_at,
        )
        for me in results
    ]


@router.get("/{estimate_id}", response_model=MarginEstimateResponse)
def get_margin_estimate_by_id(
    estimate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific margin estimate by ID (must belong to current user)"""
    margin_estimate = db.execute(
        select(MarginEstimate).where(
            MarginEstimate.id == estimate_id,
            MarginEstimate.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if not margin_estimate:
        raise HTTPException(status_code=404, detail="Margin estimate not found")

    return MarginEstimateResponse(
        id=margin_estimate.id,
        user_id=margin_estimate.user_id,
        saved_product_id=margin_estimate.saved_product_id,
        product_name=margin_estimate.product_name,
        platform=margin_estimate.platform,
        cost_price=margin_estimate.cost_price,
        selling_price=margin_estimate.selling_price,
        currency=margin_estimate.currency,
        estimated_margin=margin_estimate.estimated_margin,
        margin_percentage=margin_estimate.margin_percentage,
        notes=margin_estimate.notes,
        created_at=margin_estimate.created_at,
        updated_at=margin_estimate.updated_at,
    )


@router.put("/{estimate_id}", response_model=MarginEstimateResponse)
def update_margin_estimate(
    estimate_id: str,
    estimate_data: MarginEstimateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update a margin estimate by ID (must belong to current user).
    
    Request body (all fields optional):
    - cost_price: float
    - selling_price: float
    - notes: str
    
    Automatically recalculates estimated_margin and margin_percentage if prices updated.
    """
    margin_estimate = db.execute(
        select(MarginEstimate).where(
            MarginEstimate.id == estimate_id,
            MarginEstimate.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if not margin_estimate:
        raise HTTPException(status_code=404, detail="Margin estimate not found")

    # Update only provided fields
    update_data = estimate_data.model_dump(exclude_unset=True)
    
    # Handle cost_price and selling_price updates with margin recalculation
    if "cost_price" in update_data or "selling_price" in update_data:
        cost_price = update_data.get("cost_price", margin_estimate.cost_price)
        selling_price = update_data.get("selling_price", margin_estimate.selling_price)
        
        estimated_margin, margin_percentage = calculate_margins(cost_price, selling_price)
        margin_estimate.estimated_margin = estimated_margin
        margin_estimate.margin_percentage = margin_percentage
    
    # Update other fields
    for field in ["cost_price", "selling_price", "notes"]:
        if field in update_data:
            setattr(margin_estimate, field, update_data[field])

    db.commit()
    db.refresh(margin_estimate)

    return MarginEstimateResponse(
        id=margin_estimate.id,
        user_id=margin_estimate.user_id,
        saved_product_id=margin_estimate.saved_product_id,
        product_name=margin_estimate.product_name,
        platform=margin_estimate.platform,
        cost_price=margin_estimate.cost_price,
        selling_price=margin_estimate.selling_price,
        currency=margin_estimate.currency,
        estimated_margin=margin_estimate.estimated_margin,
        margin_percentage=margin_estimate.margin_percentage,
        notes=margin_estimate.notes,
        created_at=margin_estimate.created_at,
        updated_at=margin_estimate.updated_at,
    )


@router.delete("/{estimate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_margin_estimate(
    estimate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a margin estimate by ID (must belong to current user).
    
    Returns 204 No Content on successful deletion.
    Returns 404 if estimate not found or doesn't belong to current user.
    """
    margin_estimate = db.execute(
        select(MarginEstimate).where(
            MarginEstimate.id == estimate_id,
            MarginEstimate.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if not margin_estimate:
        raise HTTPException(status_code=404, detail="Margin estimate not found")

    db.delete(margin_estimate)
    db.commit()
