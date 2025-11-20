from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/health")
async def health_check():
    return {"status": "ok"}
