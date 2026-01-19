# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PSCC Analytics Backend"
    API_V1_PREFIX: str = "/api/v1"
    
    DATABASE_URL: str

    # 🔐 JWT-related settings
    JWT_SECRET: str = "change-this-to-a-long-random-string"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15  # 15 minutes for now
    REFRESH_TOKEN_DAYS: int = 30  # 30 days for now

    class Config:
        env_file = ".env"


settings = Settings()
