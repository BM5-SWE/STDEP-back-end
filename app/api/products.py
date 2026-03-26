from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from typing import Optional

from app.db.session import SessionLocal
from app.models.user import User
from app.models.saved_product import SavedProduct
from app.schemas.models import SavedProductCreate, SavedProductResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/saved-products", tags=["saved-products"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=SavedProductResponse, status_code=status.HTTP_201_CREATED)
def save_product(
    product_data: SavedProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save/bookmark a product to user's collection.
    
    Request body:
    - product_name: str (required)
    - platform: str (required) - "amazon" or "aliexpress"
    - platform_url: str (optional) - URL to product page
    - product_image_url: str (optional) - Product image URL
    - price: float (optional) - Current price
    - currency: str (optional) - Currency code (e.g., "USD", "CAD")
    - category: str (optional) - Product category
    - cluster_id: int (optional) - ML clustering ID from query results
    - s3_reference: str (optional) - Reference to product data in S3
    
    Returns: SavedProductResponse with created product details
    """
    # Create new SavedProduct record
    new_product = SavedProduct(
        user_id=current_user.id,
        product_name=product_data.product_name,
        platform=product_data.platform,
        platform_url=product_data.platform_url,
        product_image_url=product_data.product_image_url,
        price=product_data.price,
        currency=product_data.currency,
        category=product_data.category,
        cluster_id=product_data.cluster_id,
        s3_reference=product_data.s3_reference,
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return SavedProductResponse(
        id=new_product.id,
        user_id=new_product.user_id,
        product_name=new_product.product_name,
        platform=new_product.platform,
        platform_url=new_product.platform_url,
        product_image_url=new_product.product_image_url,
        price=new_product.price,
        currency=new_product.currency,
        category=new_product.category,
        cluster_id=new_product.cluster_id,
        s3_reference=new_product.s3_reference,
        created_at=new_product.created_at,
        updated_at=new_product.updated_at,
    )


@router.get("", response_model=list[SavedProductResponse])
def get_saved_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    platform: Optional[str] = Query(None, regex="^(amazon|aliexpress)$"),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Get current user's saved/bookmarked products.
    
    Query Parameters:
    - platform: Filter by "amazon" or "aliexpress" (optional)
    - category: Filter by product category (optional)
    - limit: Number of results (1-500, default 50)
    - offset: Pagination offset (default 0)
    """
    query = select(SavedProduct).where(
        SavedProduct.user_id == current_user.id
    )

    # Optional filters
    if platform:
        query = query.where(SavedProduct.platform == platform)
    if category:
        query = query.where(SavedProduct.category == category)

    # Order by most recently saved first, then apply pagination
    query = query.order_by(desc(SavedProduct.created_at)).limit(limit).offset(offset)

    results = db.execute(query).scalars().all()

    return [
        SavedProductResponse(
            id=sp.id,
            user_id=sp.user_id,
            product_name=sp.product_name,
            platform=sp.platform,
            platform_url=sp.platform_url,
            product_image_url=sp.product_image_url,
            price=sp.price,
            currency=sp.currency,
            category=sp.category,
            cluster_id=sp.cluster_id,
            s3_reference=sp.s3_reference,
            created_at=sp.created_at,
            updated_at=sp.updated_at,
        )
        for sp in results
    ]


@router.get("/{product_id}", response_model=SavedProductResponse)
def get_saved_product_by_id(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific saved product by ID (must belong to current user)"""
    saved_product = db.execute(
        select(SavedProduct).where(
            SavedProduct.id == product_id,
            SavedProduct.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if not saved_product:
        raise HTTPException(status_code=404, detail="Saved product not found")

    return SavedProductResponse(
        id=saved_product.id,
        user_id=saved_product.user_id,
        product_name=saved_product.product_name,
        platform=saved_product.platform,
        platform_url=saved_product.platform_url,
        product_image_url=saved_product.product_image_url,
        price=saved_product.price,
        currency=saved_product.currency,
        category=saved_product.category,
        cluster_id=saved_product.cluster_id,
        s3_reference=saved_product.s3_reference,
        created_at=saved_product.created_at,
        updated_at=saved_product.updated_at,
    )