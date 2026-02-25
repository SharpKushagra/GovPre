"""
Opportunities API router.
"""
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import func, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base import get_db
from backend.models.opportunity import Opportunity
from backend.schemas.opportunity import (
    OpportunityResponse,
    OpportunityListResponse,
)
from backend.workers.tasks import process_opportunity_documents

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


@router.get("", response_model=OpportunityListResponse)
async def list_opportunities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    naics_code: Optional[str] = Query(default=None),
    set_aside_type: Optional[str] = Query(default=None),
    active: Optional[bool] = Query(default=True),
    agency: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    List government opportunities with filtering and pagination.
    """
    query = select(Opportunity)

    if active is not None:
        query = query.where(Opportunity.active == active)
    if naics_code:
        query = query.where(Opportunity.naics_code == naics_code)
    if set_aside_type:
        query = query.where(Opportunity.set_aside_type.ilike(f"%{set_aside_type}%"))
    if agency:
        query = query.where(Opportunity.agency.ilike(f"%{agency}%"))
    if search:
        query = query.where(
            or_(
                Opportunity.title.ilike(f"%{search}%"),
                Opportunity.description.ilike(f"%{search}%"),
                Opportunity.solicitation_number.ilike(f"%{search}%"),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = (
        query.order_by(Opportunity.posted_date.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    opportunities = result.scalars().all()

    return OpportunityListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[OpportunityResponse.model_validate(o) for o in opportunities],
    )


@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single opportunity by ID.
    """
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return OpportunityResponse.model_validate(opp)


@router.post("/{opportunity_id}/process")
async def process_opportunity(
    opportunity_id: uuid.UUID,
    force: bool = Query(default=False),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger document processing for an opportunity (download PDFs, chunk, embed).
    Queues a Celery task.
    """
    result = await db.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opp = result.scalar_one_or_none()
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    task = process_opportunity_documents.delay(str(opportunity_id), force=force)

    return {
        "message": "Document processing queued",
        "opportunity_id": str(opportunity_id),
        "task_id": task.id,
    }
