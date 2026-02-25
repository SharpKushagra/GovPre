"""
DocumentChunk model — stores chunked text from solicitation documents.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from backend.db.base import Base
from backend.config import settings


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    source_file: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Vector embedding for this chunk
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        Vector(settings.EMBEDDING_DIMENSION), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    opportunity: Mapped["Opportunity"] = relationship(
        "Opportunity", back_populates="document_chunks"
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk id={self.id} opp={self.opportunity_id} idx={self.chunk_index}>"
