from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "PSCC Analytics Backend"
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
