from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.gemini import router as gemini_router
from app.api.query import router as query_router
from app.api.products import router as products_router
from app.api.margins import router as margins_router
from app.api.workflow import router as workflow_router

app = FastAPI(title="Your API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000, http://localhost:3000/, http://127.0.0.1:3000, http://127.0.0.1:3000/"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(gemini_router, prefix="/gemini", tags=["Gemini"])
app.include_router(query_router, prefix="/api", tags=["Queries"])
app.include_router(products_router, prefix="/api", tags=["Products"])
app.include_router(margins_router, prefix="/api", tags=["Margins"])
app.include_router(workflow_router, prefix="/api", tags=["Workflow"])

@app.get("/")
def root():
    return {"status": "running"}