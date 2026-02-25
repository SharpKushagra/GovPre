"""
RAG Service — Retrieval-Augmented Generation pipeline for proposal context building.
"""
import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.document_chunk import DocumentChunk
from backend.models.user_profile import UserProfile
from backend.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class RetrievedChunk:
    """Represents a chunk retrieved via vector similarity search."""

    def __init__(
        self,
        chunk_id: str,
        chunk_text: str,
        source_file: str,
        chunk_index: int,
        similarity: float,
        opportunity_id: str,
    ):
        self.chunk_id = chunk_id
        self.chunk_text = chunk_text
        self.source_file = source_file
        self.chunk_index = chunk_index
        self.similarity = similarity
        self.opportunity_id = opportunity_id

    def to_citation(self) -> str:
        """Generate a human-readable citation string."""
        section_hint = _guess_section_from_source(self.source_file, self.chunk_index)
        return f"[Source: {section_hint}]"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "source_file": self.source_file,
            "chunk_index": self.chunk_index,
            "snippet": self.chunk_text[:200] + ("..." if len(self.chunk_text) > 200 else ""),
            "citation": self.to_citation(),
            "similarity": self.similarity,
        }


def _guess_section_from_source(source_file: str, chunk_index: int) -> str:
    """Attempt to guess section label for citation."""
    if "[Description]" in source_file:
        return f"Solicitation Description, Part {chunk_index + 1}"
    name = source_file.replace(".pdf", "").replace(".PDF", "")
    name = name.replace("_", " ").replace("-", " ").strip()
    return f"{name}, Section {chunk_index + 1}"


class RAGService:
    """
    Retrieval-Augmented Generation pipeline.
    Orchestrates vector search, context assembly, and LLM generation.
    """

    async def embed_user_profile(self, profile: UserProfile) -> List[float]:
        """
        Create a combined embedding for a user profile.
        Concatenates key fields into a single document before embedding.
        """
        profile_doc = _build_profile_document(profile)
        embedding = await embedding_service.embed_text(profile_doc)
        return embedding

    async def retrieve_opportunity_chunks(
        self,
        db: AsyncSession,
        opportunity_id: uuid.UUID,
        query_embedding: List[float],
        limit: int = None,
    ) -> List[RetrievedChunk]:
        """
        STEP 2: Vector similarity search over document chunks for an opportunity.

        Uses pgvector cosine distance operator (<->) to rank chunks.
        """
        limit = limit or settings.VECTOR_SEARCH_LIMIT
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        sql = text(
            """
            SELECT
                id::text,
                chunk_text,
                source_file,
                chunk_index,
                opportunity_id::text,
                1 - (embedding <-> CAST(:query_embedding AS vector)) AS similarity
            FROM document_chunks
            WHERE opportunity_id = :opportunity_id
              AND embedding IS NOT NULL
            ORDER BY embedding <-> CAST(:query_embedding AS vector)
            LIMIT :limit
            """
        )
        result = await db.execute(
            sql,
            {
                "query_embedding": embedding_str,
                "opportunity_id": str(opportunity_id),
                "limit": limit,
            },
        )
        rows = result.fetchall()

        chunks = []
        for row in rows:
            chunks.append(
                RetrievedChunk(
                    chunk_id=row[0],
                    chunk_text=row[1],
                    source_file=row[2] or "[Unknown]",
                    chunk_index=row[3],
                    opportunity_id=row[4],
                    similarity=float(row[5]),
                )
            )
        return chunks

    async def retrieve_global_chunks(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        limit: int = 10,
    ) -> List[RetrievedChunk]:
        """
        Cross-opportunity vector search (used when a specific opportunity isn't targeted).
        """
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

        sql = text(
            """
            SELECT
                id::text,
                chunk_text,
                source_file,
                chunk_index,
                opportunity_id::text,
                1 - (embedding <-> CAST(:query_embedding AS vector)) AS similarity
            FROM document_chunks
            WHERE embedding IS NOT NULL
            ORDER BY embedding <-> CAST(:query_embedding AS vector)
            LIMIT :limit
            """
        )
        result = await db.execute(
            sql,
            {"query_embedding": embedding_str, "limit": limit},
        )
        rows = result.fetchall()

        return [
            RetrievedChunk(
                chunk_id=row[0],
                chunk_text=row[1],
                source_file=row[2] or "[Unknown]",
                chunk_index=row[3],
                opportunity_id=row[4],
                similarity=float(row[5]),
            )
            for row in rows
        ]

    def build_structured_context(
        self,
        profile: UserProfile,
        opportunity_chunks: List[RetrievedChunk],
        max_tokens: int = None,
    ) -> Dict[str, Any]:
        """
        STEP 4: Assemble structured context for the LLM.
        Returns both the context string and source metadata.
        """
        max_tokens = max_tokens or settings.MAX_CONTEXT_TOKENS

        # Build solicitation context
        solicitation_parts = []
        sources = []
        token_budget = max_tokens

        for chunk in opportunity_chunks:
            chunk_tokens = len(chunk.chunk_text.split()) * 1.3  # rough estimate
            if chunk_tokens > token_budget:
                break
            solicitation_parts.append(
                f"[{chunk.to_citation()}]\n{chunk.chunk_text}"
            )
            sources.append(chunk.to_dict())
            token_budget -= chunk_tokens  # type: ignore

        # Build user profile context
        profile_doc = _build_profile_document(profile)

        context = {
            "solicitation_context": "\n\n---\n\n".join(solicitation_parts),
            "user_profile_context": profile_doc,
            "sources": sources,
            "company_name": profile.company_name,
        }
        return context

    async def full_rag_pipeline(
        self,
        db: AsyncSession,
        opportunity_id: uuid.UUID,
        user_profile: UserProfile,
    ) -> Dict[str, Any]:
        """
        Runs the complete RAG pipeline:
        1. Embed user profile
        2. Retrieve relevant opportunity chunks (vector search)
        3. Build structured context
        Returns context dict ready for proposal generation.
        """
        logger.info(f"Starting RAG pipeline for opportunity {opportunity_id}")

        # STEP 1: Embed user profile
        query_embedding = await self.embed_user_profile(user_profile)

        # STEP 2: Retrieve relevant opportunity chunks
        opportunity_chunks = await self.retrieve_opportunity_chunks(
            db=db,
            opportunity_id=opportunity_id,
            query_embedding=query_embedding,
            limit=settings.VECTOR_SEARCH_LIMIT,
        )
        logger.info(f"Retrieved {len(opportunity_chunks)} opportunity chunks")

        # STEP 3 & 4: Build context
        context = self.build_structured_context(
            profile=user_profile,
            opportunity_chunks=opportunity_chunks,
        )
        logger.info("RAG pipeline complete")
        return context


def _build_profile_document(profile: UserProfile) -> str:
    """Build a consolidated text document from user profile for embedding."""
    parts = []

    if profile.company_name:
        parts.append(f"Company: {profile.company_name}")
    if profile.years_experience:
        parts.append(f"Years of Experience: {profile.years_experience}")
    if profile.location:
        parts.append(f"Location: {profile.location}")
    if profile.naics_codes:
        parts.append(f"NAICS Codes: {', '.join(profile.naics_codes)}")
    if profile.set_asides:
        parts.append(f"Set-Aside Eligibilities: {', '.join(profile.set_asides)}")
    if profile.certifications:
        parts.append(f"Certifications:\n{profile.certifications}")
    if profile.capabilities_statement:
        parts.append(f"Capabilities Statement:\n{profile.capabilities_statement}")
    if profile.past_performance:
        parts.append(f"Past Performance:\n{profile.past_performance}")

    return "\n\n".join(parts)


# Singleton instance
rag_service = RAGService()
