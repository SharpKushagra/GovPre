"""
Models package — imports all models so Alembic autodiscovers them.
"""
from backend.models.opportunity import Opportunity
from backend.models.document_chunk import DocumentChunk
from backend.models.user_profile import UserProfile
from backend.models.proposal import Proposal

__all__ = ["Opportunity", "DocumentChunk", "UserProfile", "Proposal"]
