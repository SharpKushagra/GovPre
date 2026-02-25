"""
Document Processor — downloads PDFs, extracts text, chunks, and embeds.
"""
import asyncio
import io
import logging
import re
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

import httpx
import tiktoken
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.document_chunk import DocumentChunk
from backend.models.opportunity import Opportunity
from backend.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

# Tiktoken encoder (cl100k_base works for GPT-4 and embedding models)
_enc = tiktoken.get_encoding("cl100k_base")

CHUNK_SIZE = settings.CHUNK_SIZE_TOKENS
CHUNK_OVERLAP = settings.CHUNK_OVERLAP_TOKENS


def _count_tokens(text: str) -> int:
    return len(_enc.encode(text))


def _clean_text(text: str) -> str:
    """Remove noise from extracted PDF text."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E\n\t]', ' ', text)
    # Remove page numbers / headers that are just numbers
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    return text.strip()


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into token-based chunks with overlap.
    """
    tokens = _enc.encode(text)
    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = _enc.decode(chunk_tokens)
        chunks.append(chunk_text)

        if end == len(tokens):
            break
        start += chunk_size - overlap

    return chunks


async def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
        loop = asyncio.get_event_loop()

        def _extract():
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            texts = []
            for page in doc:
                texts.append(page.get_text())
            doc.close()
            return "\n\n".join(texts)

        return await loop.run_in_executor(None, _extract)
    except ImportError:
        logger.warning("PyMuPDF not available, falling back to pdfplumber")
        return await _extract_text_pdfplumber(pdf_bytes)
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return ""


async def _extract_text_pdfplumber(pdf_bytes: bytes) -> str:
    """Fallback: extract text using pdfplumber."""
    try:
        import pdfplumber
        loop = asyncio.get_event_loop()

        def _extract():
            texts = []
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        texts.append(t)
            return "\n\n".join(texts)

        return await loop.run_in_executor(None, _extract)
    except Exception as e:
        logger.error(f"pdfplumber extraction error: {e}")
        return ""


async def _download_file(url: str) -> Optional[bytes]:
    """Download a file from URL, return bytes."""
    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(
                url,
                headers={"X-Api-Key": settings.SAMGOV_API_KEY},
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return None


class DocumentProcessor:
    """
    Processes solicitation documents:
    1. Downloads PDF attachments
    2. Extracts and cleans text
    3. Chunks text into token-sized pieces
    4. Embeds each chunk
    5. Stores chunks in the database
    """

    async def process_opportunity(
        self,
        db: AsyncSession,
        opportunity: Opportunity,
        force: bool = False,
    ) -> int:
        """
        Full processing pipeline for a given opportunity.
        Returns number of chunks created.
        """
        if opportunity.processed and not force:
            logger.info(f"Opportunity {opportunity.notice_id} already processed, skipping")
            return 0

        # Delete existing chunks if reprocessing
        if force:
            existing = await db.execute(
                select(DocumentChunk).where(
                    DocumentChunk.opportunity_id == opportunity.id
                )
            )
            for chunk in existing.scalars().all():
                await db.delete(chunk)
            await db.flush()

        total_chunks = 0

        # Process main description text
        if opportunity.full_text:
            chunks_created = await self._process_text(
                db=db,
                opportunity_id=opportunity.id,
                text=opportunity.full_text,
                source_file="[Description]",
            )
            total_chunks += chunks_created

        # Process attachments
        attachments = opportunity.attachments or []
        for attachment in attachments:
            file_url = attachment.get("file_url", "")
            file_name = attachment.get("file_name", "unknown")
            file_type = attachment.get("file_type", "")

            if not file_url:
                continue

            # Only process PDFs and text documents
            if not any(
                ft in file_type.lower() or file_name.lower().endswith(ext)
                for ft, ext in [("pdf", ".pdf"), ("text", ".txt"), ("word", ".docx")]
            ):
                logger.debug(f"Skipping non-text attachment: {file_name}")
                continue

            logger.info(f"Processing attachment: {file_name}")
            file_bytes = await _download_file(file_url)
            if not file_bytes:
                continue

            if "pdf" in file_type.lower() or file_name.lower().endswith(".pdf"):
                text = await _extract_text_from_pdf(file_bytes)
            else:
                try:
                    text = file_bytes.decode("utf-8", errors="ignore")
                except Exception:
                    text = ""

            if not text.strip():
                logger.warning(f"No text extracted from {file_name}")
                continue

            text = _clean_text(text)
            chunks_created = await self._process_text(
                db=db,
                opportunity_id=opportunity.id,
                text=text,
                source_file=file_name,
            )
            total_chunks += chunks_created

        # Mark opportunity as processed
        opportunity.processed = True
        await db.flush()

        logger.info(f"Processed opportunity {opportunity.notice_id}: {total_chunks} chunks created")
        return total_chunks

    async def _process_text(
        self,
        db: AsyncSession,
        opportunity_id: uuid.UUID,
        text: str,
        source_file: str,
    ) -> int:
        """
        Chunk text, embed each chunk, and store in DB.
        """
        if not text.strip():
            return 0

        chunks = _chunk_text(text)
        logger.info(f"Processing {len(chunks)} chunks for {source_file}")

        # Batch embed all chunks
        try:
            embeddings = await embedding_service.embed_batch(chunks, batch_size=20)
        except Exception as e:
            logger.error(f"Batch embedding failed for {source_file}: {e}")
            # Fall back to individual embedding with graceful degradation
            embeddings = []
            for chunk in chunks:
                try:
                    emb = await embedding_service.embed_text(chunk)
                    embeddings.append(emb)
                except Exception:
                    embeddings.append(None)

        for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            token_count = _count_tokens(chunk_text)
            chunk = DocumentChunk(
                id=uuid.uuid4(),
                opportunity_id=opportunity_id,
                chunk_text=chunk_text,
                chunk_index=i,
                source_file=source_file,
                token_count=token_count,
                embedding=embedding,
            )
            db.add(chunk)

        await db.flush()
        return len(chunks)


# Singleton instance
document_processor = DocumentProcessor()
