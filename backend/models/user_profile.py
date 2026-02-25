"""
UserProfile model — company capabilities and matching profile.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from backend.db.base import Base
from backend.config import settings


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_name: Mapped[str] = mapped_column(String(512), nullable=False)

    # Core capability docs
    capabilities_statement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    past_performance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certifications: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # NAICS codes
    naics_codes: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Set-aside eligibilities (e.g., 8(a), HUBZone, SDVOSB)
    set_asides: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Location info
    location: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Experience
    years_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Combined profile embedding for semantic matching
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSION), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    proposals: Mapped[List["Proposal"]] = relationship(
        "Proposal", back_populates="user_profile"
    )

    def __repr__(self) -> str:
        return f"<UserProfile id={self.id} company={self.company_name}>"
