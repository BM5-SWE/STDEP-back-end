from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


# SavedProduct Schemas
class SavedProductCreate(BaseModel):
    product_name: str
    platform: str = Field(pattern="^(amazon|aliexpress)$")
    platform_url: Optional[str] = None
    product_image_url: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    cluster_id: Optional[int] = None
    s3_reference: Optional[str] = None


class SavedProductUpdate(BaseModel):
    product_name: Optional[str] = None
    platform_url: Optional[str] = None
    product_image_url: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    category: Optional[str] = None
    s3_reference: Optional[str] = None


class SavedProductResponse(BaseModel):
    id: UUID
    user_id: UUID
    product_name: str
    platform: str
    platform_url: Optional[str]
    product_image_url: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    category: Optional[str]
    cluster_id: Optional[int]
    s3_reference: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# QueryHistory Schemas
class QueryHistoryCreate(BaseModel):
    query_text: str = Field(max_length=500)
    platform: str = Field(pattern="^(amazon|aliexpress)$")
    query_type: str = Field(pattern="^(category|custom)$")
    s3_result_key: Optional[str] = None
    result_cached_at: Optional[datetime] = None
    total_products_returned: Optional[int] = None
    num_clusters: Optional[int] = None


class QueryHistoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    query_text: str
    platform: str
    query_type: str
    s3_result_key: Optional[str]
    result_cached_at: Optional[datetime]
    total_products_returned: Optional[int]
    num_clusters: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# MarginEstimate Schemas
class MarginEstimateCreate(BaseModel):
    product_name: str
    platform: str = Field(pattern="^(amazon|aliexpress)$")
    cost_price: float = Field(gt=0)
    selling_price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = None
    saved_product_id: Optional[UUID] = None
    notes: Optional[str] = None


class MarginEstimateUpdate(BaseModel):
    cost_price: Optional[float] = Field(None, gt=0)
    selling_price: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class MarginEstimateResponse(BaseModel):
    id: UUID
    user_id: UUID
    saved_product_id: Optional[UUID]
    product_name: str
    platform: str
    cost_price: float
    selling_price: Optional[float]
    currency: Optional[str]
    estimated_margin: Optional[float]
    margin_percentage: Optional[float]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
