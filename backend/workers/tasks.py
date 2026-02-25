"""
Celery tasks — async processing for document ingestion, embedding, and proposal generation.
"""
import asyncio
import logging
import uuid
from typing import Optional

from celery import shared_task

from backend.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Helper to run async code in a Celery task (synchronous context)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            from backend.db.base import engine
            loop.run_until_complete(engine.dispose())
        except Exception:
            pass
        loop.close()


@celery_app.task(
    bind=True,
    name="backend.workers.tasks.ingest_samgov_opportunities",
    max_retries=3,
    default_retry_delay=300,
)
def ingest_samgov_opportunities(self, max_pages: int = 10):
    """
    Periodic task: Fetch and store SAM.gov opportunities.
    Runs every 6 hours via Celery Beat.
    """
    async def _inner():
        from backend.db.base import AsyncSessionLocal
        from backend.services.samgov_service import samgov_service

        async with AsyncSessionLocal() as db:
            try:
                count = await samgov_service.run_full_ingestion(db, max_pages=max_pages)
                logger.info(f"SAM.gov ingestion complete: {count} records processed")
                return {"status": "success", "count": count}
            except Exception as e:
                logger.error(f"SAM.gov ingestion failed: {e}")
                raise self.retry(exc=e)

    return _run_async(_inner())


@celery_app.task(
    bind=True,
    name="backend.workers.tasks.process_opportunity_documents",
    max_retries=3,
    default_retry_delay=60,
)
def process_opportunity_documents(self, opportunity_id: str, force: bool = False):
    """
    Async task: Download attachments, extract text, chunk, and embed.
    """
    async def _inner():
        from backend.db.base import AsyncSessionLocal
        from backend.models.opportunity import Opportunity
        from backend.services.document_processor import document_processor
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            try:
                result = await db.execute(
                    select(Opportunity).where(
                        Opportunity.id == uuid.UUID(opportunity_id)
                    )
                )
                opportunity = result.scalar_one_or_none()
                if not opportunity:
                    logger.error(f"Opportunity {opportunity_id} not found")
                    return {"status": "error", "message": "Opportunity not found"}

                chunks = await document_processor.process_opportunity(db, opportunity, force=force)
                await db.commit()

                logger.info(f"Processed opportunity {opportunity_id}: {chunks} chunks")
                return {"status": "success", "chunks": chunks}
            except Exception as e:
                logger.error(f"Document processing failed: {e}", exc_info=True)
                await db.rollback()
                raise self.retry(exc=e)

    return _run_async(_inner())


@celery_app.task(
    bind=True,
    name="backend.workers.tasks.generate_proposal_async",
    max_retries=2,
    default_retry_delay=30,
    time_limit=600,  # 10 minute max
)
def generate_proposal_async(
    self,
    proposal_id: str,
    opportunity_id: str,
    user_profile_id: str,
    tone: str = "professional",
):
    """
    Async task: Run the full RAG + LLM proposal generation pipeline.
    """
    async def _inner():
        from backend.db.base import AsyncSessionLocal
        from backend.models.proposal import Proposal
        from backend.services.proposal_service import proposal_service
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            try:
                # Update task_id on the proposal
                result = await db.execute(
                    select(Proposal).where(Proposal.id == uuid.UUID(proposal_id))
                )
                proposal = result.scalar_one_or_none()
                if proposal:
                    proposal.task_id = self.request.id
                    await db.flush()

                # Generate the proposal
                updated_proposal = await proposal_service.generate_proposal(
                    db=db,
                    opportunity_id=uuid.UUID(opportunity_id),
                    user_profile_id=uuid.UUID(user_profile_id),
                    tone=tone,
                    proposal_id=uuid.UUID(proposal_id),
                )
                await db.commit()

                return {
                    "status": updated_proposal.status,
                    "proposal_id": str(updated_proposal.id),
                }
            except Exception as e:
                logger.error(f"Proposal generation task failed: {e}", exc_info=True)
                await db.rollback()

                # Mark proposal as failed
                async with AsyncSessionLocal() as db2:
                    res = await db2.execute(
                        select(Proposal).where(Proposal.id == uuid.UUID(proposal_id))
                    )
                    p = res.scalar_one_or_none()
                    if p:
                        p.status = "failed"
                        p.error_message = str(e)
                        await db2.commit()

                raise self.retry(exc=e)

    return _run_async(_inner())


@celery_app.task(
    name="backend.workers.tasks.mark_expired_opportunities",
)
def mark_expired_opportunities():
    """Daily task: Mark expired opportunities as inactive."""
    async def _inner():
        from backend.db.base import AsyncSessionLocal
        from backend.services.samgov_service import samgov_service

        async with AsyncSessionLocal() as db:
            count = await samgov_service.mark_expired_inactive(db)
            await db.commit()
            return {"status": "success", "marked_inactive": count}

    return _run_async(_inner())


@celery_app.task(
    name="backend.workers.tasks.embed_user_profile",
)
def embed_user_profile(user_profile_id: str):
    """Embed a user profile for opportunity matching."""
    async def _inner():
        from backend.db.base import AsyncSessionLocal
        from backend.models.user_profile import UserProfile
        from backend.services.rag_service import rag_service
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UserProfile).where(UserProfile.id == uuid.UUID(user_profile_id))
            )
            profile = result.scalar_one_or_none()
            if not profile:
                return {"status": "error", "message": "Profile not found"}

            embedding = await rag_service.embed_user_profile(profile)
            profile.embedding = embedding
            await db.commit()
            return {"status": "success"}

    return _run_async(_inner())
