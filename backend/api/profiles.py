"""
User Profiles API router.
"""
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base import get_db
from backend.models.user_profile import UserProfile
from backend.schemas.user_profile import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
)
from backend.workers.tasks import embed_user_profile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profiles", tags=["User Profiles"])


@router.post("", response_model=UserProfileResponse, status_code=201)
async def create_profile(
    payload: UserProfileCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new company/user profile."""
    profile = UserProfile(id=uuid.uuid4(), **payload.model_dump())
    db.add(profile)
    await db.flush()

    # Queue background embedding
    embed_user_profile.delay(str(profile.id))

    return UserProfileResponse.model_validate(profile)


@router.get("/{profile_id}", response_model=UserProfileResponse)
async def get_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a user profile by ID."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return UserProfileResponse.model_validate(profile)


@router.patch("/{profile_id}", response_model=UserProfileResponse)
async def update_profile(
    profile_id: uuid.UUID,
    payload: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing user profile."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.flush()

    # Re-embed on update
    embed_user_profile.delay(str(profile_id))

    return UserProfileResponse.model_validate(profile)


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a user profile."""
    result = await db.execute(
        select(UserProfile).where(UserProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    await db.delete(profile)
