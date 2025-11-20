from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login():
    # TODO: replace with real auth (DB, JWT, etc.)
    return {"access_token": "fake-token", "token_type": "bearer"}
