"""
Core dependencies — reusable FastAPI dependency injectors.
"""
from typing import AsyncGenerator

from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.base import AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency: provides a scoped async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_api_key(x_api_key: str = Header(default="")) -> str:
    """Optional: validate internal API key for protected routes."""
    # In production, validate against a real secret
    return x_api_key
