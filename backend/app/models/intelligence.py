from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class AssistantQueryLog(Base):
    __tablename__ = "assistant_query_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    intent: Mapped[str] = mapped_column(String(60), nullable=False)
    tool: Mapped[str] = mapped_column(String(80), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User")
