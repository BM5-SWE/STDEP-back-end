from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

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
