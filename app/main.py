from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router

app = FastAPI(title="Your API")

app.include_router(auth_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",          # local frontend
        "http://127.0.0.1:3000",
        "http://3.98.120.213:3000",      # if frontend ever runs on EC2
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)