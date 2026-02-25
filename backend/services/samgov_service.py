"""
SAM.gov Ingestion Service — fetches, stores, and updates government opportunities.
"""
import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.opportunity import Opportunity
from backend.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

SAMGOV_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    """Parse SAM.gov date strings into datetime objects."""
    if not value:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    logger.warning(f"Could not parse date: {value}")
    return None


def _extract_opportunity_data(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Map SAM.gov API response fields to our Opportunity model."""
    # SAM.gov API v2 field names
    attachments = []
    for res in raw.get("resourceLinks", []) or []:
        attachments.append(
            {
                "file_name": res.get("name", ""),
                "file_url": res.get("uri", ""),
                "file_type": res.get("mimeType", ""),
            }
        )

    place_of_performance = ""
    pop = raw.get("placeOfPerformance", {}) or {}
    if pop:
        parts = [
            pop.get("city", {}).get("name", ""),
            pop.get("state", {}).get("code", ""),
            pop.get("country", {}).get("code", ""),
        ]
        place_of_performance = ", ".join(p for p in parts if p)

    full_text_parts = [
        raw.get("title", ""),
        raw.get("description", ""),
    ]
    full_text = "\n\n".join(p for p in full_text_parts if p)

    return {
        "notice_id": raw.get("noticeId", ""),
        "title": raw.get("title", "Untitled Opportunity"),
        "description": raw.get("description", ""),
        "agency": raw.get("fullParentPathName", ""),
        "sub_agency": raw.get("organizationHierarchy", [{}])[0].get("name") if raw.get("organizationHierarchy") else None,
        "department": raw.get("department", {}).get("name") if raw.get("department") else None,
        "posted_date": _parse_dt(raw.get("postedDate")),
        "response_deadline": _parse_dt(raw.get("responseDeadLine")),
        "archive_date": _parse_dt(raw.get("archiveDate")),
        "last_modified_date": _parse_dt(raw.get("modifiedDate") or raw.get("modifiedOn")),
        "notice_type": raw.get("type", {}).get("value") if isinstance(raw.get("type"), dict) else raw.get("type"),
        "solicitation_number": raw.get("solicitationNumber"),
        "naics_code": raw.get("naicsCode"),
        "naics_description": raw.get("classificationCode"),
        "set_aside_type": raw.get("typeOfSetAside"),
        "place_of_performance": place_of_performance,
        "contract_type": raw.get("contractType"),
        "estimated_value": raw.get("award", {}).get("amount") if raw.get("award") else None,
        "attachments": attachments,
        "full_text": full_text,
        "active": raw.get("active", "Yes") in ("Yes", True, "true", "1"),
    }


class SAMGovService:
    """
    Handles all SAM.gov API interactions and data persistence.
    """

    def __init__(self):
        self.base_url = settings.SAMGOV_BASE_URL
        self.api_key = settings.SAMGOV_API_KEY
        self.timeout = httpx.Timeout(30.0)

    def _get_headers(self) -> Dict[str, str]:
        return {"Accept": "application/json", "X-Api-Key": self.api_key}

    async def fetch_opportunities(
        self,
        limit: int = 100,
        offset: int = 0,
        posted_from: Optional[str] = None,
        posted_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch active opportunities from SAM.gov.
        """
        params: Dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "ptype": "o,p,k,r",  # solicitations
            "active": "Yes",
        }
        if posted_from:
            params["postedFrom"] = posted_from
        if posted_to:
            params["postedTo"] = posted_to

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    self.base_url,
                    params=params,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json()
                return data.get("opportunitiesData", []) or []
            except httpx.HTTPStatusError as e:
                logger.error(f"SAM.gov API HTTP error: {e.response.status_code} — {e.response.text[:500]}")
                raise
            except Exception as e:
                logger.error(f"SAM.gov fetch error: {e}")
                raise

    async def fetch_modified_opportunities(
        self, modified_from: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetch recently modified opportunities for delta updates.
        """
        params: Dict[str, Any] = {
            "limit": limit,
            "modifiedFrom": modified_from,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    self.base_url,
                    params=params,
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                data = response.json()
                return data.get("opportunitiesData", []) or []
            except Exception as e:
                logger.error(f"SAM.gov modified fetch error: {e}")
                raise

    async def download_attachments(self, notice_id: str) -> List[Dict[str, Any]]:
        """
        Download attachment metadata for a given notice.
        Returns list of {file_name, file_url, file_type}.
        """
        url = f"https://api.sam.gov/opportunities/v1/resources?noticeId={notice_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                files = []
                for item in data.get("attachments", []) or []:
                    files.append(
                        {
                            "file_name": item.get("name", ""),
                            "file_url": item.get("uri", ""),
                            "file_type": item.get("mimeType", "application/octet-stream"),
                        }
                    )
                return files
            except Exception as e:
                logger.warning(f"Could not fetch attachments for {notice_id}: {e}")
                return []

    async def store_opportunity(
        self, db: AsyncSession, raw: Dict[str, Any], generate_embedding: bool = True
    ) -> Optional[Opportunity]:
        """
        Persist a new opportunity to the database.
        Skips if notice_id already exists.
        """
        data = _extract_opportunity_data(raw)
        notice_id = data.get("notice_id", "")
        if not notice_id:
            logger.warning("Skipping opportunity with no notice_id")
            return None

        # Check for existing record
        existing = await db.execute(
            select(Opportunity).where(Opportunity.notice_id == notice_id)
        )
        existing_opp = existing.scalar_one_or_none()
        if existing_opp:
            return await self.update_opportunity(db, existing_opp, data)

        opp = Opportunity(**data, id=uuid.uuid4())

        # Generate embedding from full_text
        if generate_embedding and opp.full_text:
            try:
                opp.embedding = await embedding_service.embed_text(opp.full_text[:8000])
            except Exception as e:
                logger.warning(f"Embedding failed for {notice_id}: {e}")

        db.add(opp)
        await db.flush()
        logger.info(f"Stored new opportunity: {notice_id}")
        return opp

    async def update_opportunity(
        self,
        db: AsyncSession,
        existing: Opportunity,
        data: Dict[str, Any],
    ) -> Opportunity:
        """
        Update an existing opportunity if it has been modified.
        """
        new_modified = data.get("last_modified_date")
        if new_modified and existing.last_modified_date:
            if new_modified <= existing.last_modified_date:
                logger.debug(f"Opportunity {existing.notice_id} is current, skipping update")
                return existing

        updatable_fields = [
            "title", "description", "response_deadline", "archive_date",
            "last_modified_date", "attachments", "full_text", "active",
            "estimated_value", "set_aside_type",
        ]
        changed = False
        for field in updatable_fields:
            if field in data and getattr(existing, field) != data[field]:
                setattr(existing, field, data[field])
                changed = True

        if changed:
            if existing.full_text:
                try:
                    existing.embedding = await embedding_service.embed_text(
                        existing.full_text[:8000]
                    )
                except Exception as e:
                    logger.warning(f"Re-embedding failed for {existing.notice_id}: {e}")

            await db.flush()
            logger.info(f"Updated opportunity: {existing.notice_id}")

        return existing

    async def mark_expired_inactive(self, db: AsyncSession) -> int:
        """
        Mark opportunities whose archive_date has passed as inactive.
        """
        now = datetime.now(timezone.utc)
        result = await db.execute(
            update(Opportunity)
            .where(Opportunity.archive_date < now, Opportunity.active == True)  # noqa
            .values(active=False)
            .returning(Opportunity.id)
        )
        expired = result.fetchall()
        count = len(expired)
        if count > 0:
            logger.info(f"Marked {count} opportunities as inactive (expired)")
        return count

    async def run_full_ingestion(self, db: AsyncSession, max_pages: int = 10) -> int:
        """
        Full ingestion run: fetch all active opportunities and store them.
        """
        total_stored = 0
        page_size = 100

        for page in range(max_pages):
            offset = page * page_size
            logger.info(f"Fetching SAM.gov page {page + 1} (offset={offset})")
            try:
                raw_opps = await self.fetch_opportunities(limit=page_size, offset=offset)
            except Exception as e:
                logger.error(f"Failed to fetch page {page}: {e}")
                break

            if not raw_opps:
                logger.info("No more opportunities, stopping ingestion")
                break

            for raw in raw_opps:
                try:
                    opp = await self.store_opportunity(db, raw)
                    if opp:
                        total_stored += 1
                except Exception as e:
                    logger.error(f"Failed to store opportunity: {e}")

            await db.commit()
            await asyncio.sleep(1)  # Respectful rate limiting

        await self.mark_expired_inactive(db)
        await db.commit()
        logger.info(f"Ingestion complete. Total stored/updated: {total_stored}")
        return total_stored


# Singleton instance
samgov_service = SAMGovService()
