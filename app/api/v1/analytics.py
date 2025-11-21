# app/api/v1/analytics.py
from fastapi import APIRouter, Depends

from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/me")
async def read_me(current_user: dict = Depends(get_current_user)):
    """Example protected endpoint to test JWT auth."""
    return {
        "email": current_user["email"],
        "full_name": current_user["full_name"],
    }
