"""
Opportunity model — maps to the government opportunities ingested from SAM.gov.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from backend.db.base import Base
from backend.config import settings


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    notice_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Agency hierarchy
    agency: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    sub_agency: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Dates
    posted_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    response_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    archive_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_modified_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Notice details
    notice_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    solicitation_number: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # NAICS
    naics_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    naics_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Set-aside and place
    set_aside_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    place_of_performance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Contract info
    contract_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    estimated_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Attachments stored as JSONB array
    attachments: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=list)

    # Full text content from description + attachments
    full_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Vector embedding for opportunity matching
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSION), nullable=True
    )

    # Status
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    document_chunks: Mapped[List["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="opportunity", cascade="all, delete-orphan"
    )
    proposals: Mapped[List["Proposal"]] = relationship(
        "Proposal", back_populates="opportunity"
    )

    def __repr__(self) -> str:
        return f"<Opportunity id={self.id} notice_id={self.notice_id} title={self.title[:50]}>"
