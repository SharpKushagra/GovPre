"""
Proposal model — stores generated government proposals.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Status: pending | processing | completed | failed
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)

    # Proposal sections stored as structured JSON
    # {
    #   "executive_summary": { "content": "...", "sources": [...] },
    #   "technical_approach": { "content": "...", "sources": [...] },
    #   "past_performance": { "content": "...", "sources": [...] },
    #   "compliance_matrix": { "content": "...", "sources": [...] },
    #   "company_overview": { "content": "...", "sources": [...] },
    #   "conclusion": { "content": "...", "sources": [...] }
    # }
    sections: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Metadata
    tone: Mapped[str] = mapped_column(String(50), default="professional", nullable=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Celery task ID
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    opportunity: Mapped["Opportunity"] = relationship(
        "Opportunity", back_populates="proposals"
    )
    user_profile: Mapped["UserProfile"] = relationship(
        "UserProfile", back_populates="proposals"
    )

    def __repr__(self) -> str:
        return f"<Proposal id={self.id} status={self.status}>"
