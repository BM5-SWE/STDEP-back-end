# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "PSCC Analytics Backend"
    API_V1_PREFIX: str = "/api/v1"

    # DATABASE_URL: str
    
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_SSL: str = "require"

    # 🔐 JWT-related settings
    JWT_SECRET: str
    JWT_ALG: str
    ACCESS_TOKEN_MINUTES: int
    REFRESH_TOKEN_DAYS: int
    
    # Gemini API
    gemini_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
