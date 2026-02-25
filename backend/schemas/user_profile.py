"""
Pydantic schemas for UserProfile.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class UserProfileBase(BaseModel):
    company_name: str
    capabilities_statement: Optional[str] = None
    past_performance: Optional[str] = None
    certifications: Optional[str] = None
    naics_codes: Optional[List[str]] = None
    set_asides: Optional[List[str]] = None
    location: Optional[str] = None
    years_experience: Optional[int] = None


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    capabilities_statement: Optional[str] = None
    past_performance: Optional[str] = None
    certifications: Optional[str] = None
    naics_codes: Optional[List[str]] = None
    set_asides: Optional[List[str]] = None
    location: Optional[str] = None
    years_experience: Optional[int] = None


class UserProfileResponse(UserProfileBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
