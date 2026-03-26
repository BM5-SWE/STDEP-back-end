import uuid
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class QueryHistory(Base):
    """User's recent query history for search suggestions (like Google/YouTube search history)"""
    __tablename__ = "query_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # The actual query text
    query_text: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Context about the query
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # "amazon" or "aliexpress"
    query_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "category" or "custom"

    # Reference to cached S3 results (for avoiding re-running same query)
    s3_result_key: Mapped[str] = mapped_column(String(500), nullable=True)
    result_cached_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Summary stats (for display in history)
    total_products_returned: Mapped[int] = mapped_column(nullable=True)
    num_clusters: Mapped[int] = mapped_column(nullable=True)

    # Timestamps
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
