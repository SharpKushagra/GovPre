"""
Proposals API router — generate, retrieve, refine proposals.
"""
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base import get_db
from backend.models.proposal import Proposal
from backend.schemas.proposal import (
    GenerateProposalRequest,
    RefineProposalRequest,
    ProposalResponse,
    ProposalStatusResponse,
)
from backend.workers.tasks import generate_proposal_async

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/proposals", tags=["Proposals"])


@router.post("/generate", response_model=ProposalStatusResponse, status_code=202)
async def generate_proposal(
    payload: GenerateProposalRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a proposal generation request.
    Creates a Proposal record and queues async LLM generation via Celery.
    Returns the proposal ID and task ID for polling.
    """
    from backend.models.opportunity import Opportunity
    from backend.models.user_profile import UserProfile

    # Validate opportunity exists
    opp = await db.execute(
        select(Opportunity).where(Opportunity.id == payload.opportunity_id)
    )
    if not opp.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Validate profile exists
    profile = await db.execute(
        select(UserProfile).where(UserProfile.id == payload.user_profile_id)
    )
    if not profile.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User profile not found")

    # Create proposal record
    proposal = Proposal(
        id=uuid.uuid4(),
        opportunity_id=payload.opportunity_id,
        user_profile_id=payload.user_profile_id,
        status="pending",
        tone=payload.tone,
    )
    db.add(proposal)
    await db.flush()
    await db.commit()

    # Queue async generation
    task = generate_proposal_async.delay(
        proposal_id=str(proposal.id),
        opportunity_id=str(payload.opportunity_id),
        user_profile_id=str(payload.user_profile_id),
        tone=payload.tone,
    )

    # Store task ID
    proposal.task_id = task.id
    await db.commit()

    return ProposalStatusResponse(
        proposal_id=proposal.id,
        status=proposal.status,
        task_id=task.id,
    )


@router.get("/{proposal_id}", response_model=ProposalResponse)
async def get_proposal(
    proposal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a proposal by ID. Poll this endpoint to check generation status.
    """
    result = await db.execute(
        select(Proposal).where(Proposal.id == proposal_id)
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return ProposalResponse.model_validate(proposal)


@router.post("/refine", response_model=ProposalResponse)
async def refine_proposal(
    payload: RefineProposalRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refine a specific section of an existing proposal using a natural language instruction.
    This runs synchronously (suitable for quick refinements).
    """
    from backend.services.proposal_service import proposal_service

    result = await db.execute(
        select(Proposal).where(Proposal.id == payload.proposal_id)
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    valid_sections = [
        "executive_summary", "technical_approach", "past_performance",
        "compliance_matrix", "company_overview", "conclusion",
    ]
    if payload.section not in valid_sections:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid section. Must be one of: {valid_sections}",
        )

    try:
        updated = await proposal_service.refine_section(
            db=db,
            proposal_id=payload.proposal_id,
            section=payload.section,
            instruction=payload.instruction,
            tone=payload.tone,
        )
        await db.commit()
        return ProposalResponse.model_validate(updated)
    except Exception as e:
        logger.error(f"Section refinement failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{proposal_id}/section/{section}")
async def update_section_content(
    proposal_id: uuid.UUID,
    section: str,
    content: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Directly update section content (user manual edits).
    """
    result = await db.execute(
        select(Proposal).where(Proposal.id == proposal_id)
    )
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    sections = dict(proposal.sections or {})
    if section not in sections:
        sections[section] = {}
    sections[section]["content"] = content
    proposal.sections = sections
    proposal.version += 1
    await db.flush()

    return {"message": "Section updated", "section": section, "version": proposal.version}
