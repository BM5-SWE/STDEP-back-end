from sqlalchemy import ForeignKey, String, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    # store hash of refresh token (never store plaintext)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())