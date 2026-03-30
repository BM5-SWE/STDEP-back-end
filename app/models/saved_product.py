import uuid
from sqlalchemy import String, DateTime, func, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base


class SavedProduct(Base):
    """User-bookmarked products for quick reference"""
    __tablename__ = "saved_products"

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

    # Product metadata (not full product data - that's in S3)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # "amazon" or "aliexpress"
    platform_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    product_image_url: Mapped[str] = mapped_column(String(1000), nullable=True)

    # Price snapshot at time of bookmark
    price: Mapped[float] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=True)

    # Context
    category: Mapped[str] = mapped_column(String(255), nullable=True)
    cluster_id: Mapped[int] = mapped_column(nullable=True)

    # Reference to where full product data is stored in S3 (if needed)
    s3_reference: Mapped[str] = mapped_column(String(500), nullable=True)

    # Snapshot of all scores & stats at time of bookmark
    scores: Mapped[dict] = mapped_column(JSONB, nullable=True)

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
