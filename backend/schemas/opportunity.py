"""
Pydantic schemas for Opportunity request/response.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AttachmentSchema(BaseModel):
    file_name: str
    file_url: str
    file_type: str


class OpportunityBase(BaseModel):
    notice_id: str
    title: str
    description: Optional[str] = None
    agency: Optional[str] = None
    sub_agency: Optional[str] = None
    department: Optional[str] = None
    posted_date: Optional[datetime] = None
    response_deadline: Optional[datetime] = None
    archive_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None
    notice_type: Optional[str] = None
    solicitation_number: Optional[str] = None
    naics_code: Optional[str] = None
    naics_description: Optional[str] = None
    set_aside_type: Optional[str] = None
    place_of_performance: Optional[str] = None
    contract_type: Optional[str] = None
    estimated_value: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    active: bool = True


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    response_deadline: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None
    active: Optional[bool] = None
    estimated_value: Optional[str] = None


class OpportunityResponse(OpportunityBase):
    id: uuid.UUID
    full_text: Optional[str] = None
    processed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OpportunityListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[OpportunityResponse]


class OpportunityFilter(BaseModel):
    naics_code: Optional[str] = None
    set_aside_type: Optional[str] = None
    active: Optional[bool] = True
    agency: Optional[str] = None
    search: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
