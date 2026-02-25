"""
Ingestion API — manual triggers for SAM.gov sync.
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base import get_db
from backend.workers.tasks import ingest_samgov_opportunities, mark_expired_opportunities

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingestion", tags=["Ingestion"])


@router.post("/trigger-samgov")
async def trigger_samgov_ingestion(max_pages: int = 5):
    """
    Manually trigger a SAM.gov ingestion run.
    Queues a Celery task.
    """
    task = ingest_samgov_opportunities.delay(max_pages=max_pages)
    return {
        "message": "SAM.gov ingestion triggered",
        "task_id": task.id,
    }


@router.post("/trigger-expire")
async def trigger_mark_expired():
    """
    Manually trigger marking expired opportunities as inactive.
    """
    task = mark_expired_opportunities.delay()
    return {
        "message": "Expiry job triggered",
        "task_id": task.id,
    }
