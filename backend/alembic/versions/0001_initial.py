"""Initial migration — create pgvector extension and all tables.

Revision ID: 0001_initial
Revises: 
Create Date: 2026-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 384  # sentence-transformers/all-MiniLM-L6-v2


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── opportunities ────────────────────────────────────────────────────────
    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("notice_id", sa.String(255), nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("agency", sa.String(512)),
        sa.Column("sub_agency", sa.String(512)),
        sa.Column("department", sa.String(512)),
        sa.Column("posted_date", sa.DateTime(timezone=True)),
        sa.Column("response_deadline", sa.DateTime(timezone=True)),
        sa.Column("archive_date", sa.DateTime(timezone=True)),
        sa.Column("last_modified_date", sa.DateTime(timezone=True)),
        sa.Column("notice_type", sa.String(100)),
        sa.Column("solicitation_number", sa.String(255)),
        sa.Column("naics_code", sa.String(20)),
        sa.Column("naics_description", sa.Text),
        sa.Column("set_aside_type", sa.String(255)),
        sa.Column("place_of_performance", sa.Text),
        sa.Column("contract_type", sa.String(100)),
        sa.Column("estimated_value", sa.String(255)),
        sa.Column("attachments", postgresql.JSONB),
        sa.Column("full_text", sa.Text),
        sa.Column("embedding", Vector(EMBEDDING_DIM)),
        sa.Column("active", sa.Boolean, default=True, nullable=False),
        sa.Column("processed", sa.Boolean, default=False, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_opportunities_notice_id", "opportunities", ["notice_id"], unique=True)
    op.create_index("ix_opportunities_naics_code", "opportunities", ["naics_code"])
    op.create_index("ix_opportunities_solicitation_number", "opportunities", ["solicitation_number"])

    # pgvector HNSW index for fast ANN search
    op.execute(
        "CREATE INDEX ix_opportunities_embedding ON opportunities "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # ── user_profiles ────────────────────────────────────────────────────────
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("company_name", sa.String(512), nullable=False),
        sa.Column("capabilities_statement", sa.Text),
        sa.Column("past_performance", sa.Text),
        sa.Column("certifications", sa.Text),
        sa.Column("naics_codes", postgresql.ARRAY(sa.String)),
        sa.Column("set_asides", postgresql.ARRAY(sa.String)),
        sa.Column("location", sa.String(512)),
        sa.Column("years_experience", sa.Integer),
        sa.Column("embedding", Vector(EMBEDDING_DIM)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── document_chunks ──────────────────────────────────────────────────────
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "opportunity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("source_file", sa.String(512)),
        sa.Column("token_count", sa.Integer),
        sa.Column("embedding", Vector(EMBEDDING_DIM)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_document_chunks_opportunity_id", "document_chunks", ["opportunity_id"])
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding ON document_chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )

    # ── proposals ────────────────────────────────────────────────────────────
    op.create_table(
        "proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "opportunity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), default="pending", nullable=False),
        sa.Column("sections", postgresql.JSONB),
        sa.Column("tone", sa.String(50), default="professional", nullable=False),
        sa.Column("version", sa.Integer, default=1, nullable=False),
        sa.Column("task_id", sa.String(255)),
        sa.Column("error_message", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_proposals_opportunity_id", "proposals", ["opportunity_id"])
    op.create_index("ix_proposals_user_profile_id", "proposals", ["user_profile_id"])


def downgrade() -> None:
    op.drop_table("proposals")
    op.drop_table("document_chunks")
    op.drop_table("user_profiles")
    op.drop_table("opportunities")
    op.execute("DROP EXTENSION IF EXISTS vector")
