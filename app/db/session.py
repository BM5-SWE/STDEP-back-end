from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./dev.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite with FastAPI
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
