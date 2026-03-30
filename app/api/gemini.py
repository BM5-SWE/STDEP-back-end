from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.gemini import generate_product_estimate

router = APIRouter()

class ProductEstimateRequest(BaseModel):
    product_name: str
    brand: str
    category: str
    price: float

@router.post("/estimate")
def estimate(req: ProductEstimateRequest):
    try:
        result = generate_product_estimate(
            product_name=req.product_name,
            brand=req.brand,
            category=req.category,
            price=req.price,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Gemini estimation failed. Please try again later.") from exc

    return result