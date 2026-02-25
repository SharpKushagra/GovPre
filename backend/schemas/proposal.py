"""
Pydantic schemas for Proposal.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ProposalSectionSource(BaseModel):
    chunk_id: Optional[str] = None
    source_file: Optional[str] = None
    chunk_index: Optional[int] = None
    snippet: Optional[str] = None
    citation: str  # e.g. "[Source: Solicitation Section 3.2]"


class ProposalSection(BaseModel):
    content: str
    sources: List[ProposalSectionSource] = []


class ProposalSections(BaseModel):
    executive_summary: Optional[ProposalSection] = None
    technical_approach: Optional[ProposalSection] = None
    past_performance: Optional[ProposalSection] = None
    compliance_matrix: Optional[ProposalSection] = None
    company_overview: Optional[ProposalSection] = None
    conclusion: Optional[ProposalSection] = None


class GenerateProposalRequest(BaseModel):
    opportunity_id: uuid.UUID
    user_profile_id: uuid.UUID
    tone: str = "professional"


class RefineProposalRequest(BaseModel):
    proposal_id: uuid.UUID
    section: str  # e.g. "technical_approach"
    instruction: str  # e.g. "Make this more concise"
    tone: Optional[str] = None


class ProposalResponse(BaseModel):
    id: uuid.UUID
    opportunity_id: uuid.UUID
    user_profile_id: uuid.UUID
    status: str
    sections: Optional[Dict[str, Any]] = None
    tone: str
    version: int
    task_id: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProposalStatusResponse(BaseModel):
    proposal_id: uuid.UUID
    status: str
    task_id: Optional[str] = None
    error_message: Optional[str] = None
