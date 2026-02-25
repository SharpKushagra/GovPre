"""
Embedding Service — abstraction over OpenAI / Gemini embedding APIs.
"""
import asyncio
from typing import List, Optional
import logging

from backend.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Unified embedding interface for OpenAI and Gemini."""

    def __init__(self):
        self.provider = settings.AI_PROVIDER
        self._client = None
        self._sentence_model = None

    def _get_sentence_model(self):
        if self._sentence_model is None:
            from sentence_transformers import SentenceTransformer
            self._sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        return self._sentence_model

    def _get_openai_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def _get_gemini_client(self):
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._client = genai
        return self._client

    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        # Truncate to avoid token limits
        text = text[:30000]

        if self.provider == "openai":
            return await self._embed_openai(text)
        elif self.provider == "gemini":
            return await self._embed_gemini(text)
        elif self.provider == "groq":
            return await self._embed_groq(text)
        else:
            raise ValueError(f"Unknown AI provider: {self.provider}")

    async def embed_batch(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """Embed multiple texts in batches."""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i: i + batch_size]
            batch_embeddings = await asyncio.gather(
                *[self.embed_text(t) for t in batch]
            )
            embeddings.extend(batch_embeddings)
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)  # Rate limiting buffer
        return embeddings

    async def _embed_openai(self, text: str) -> List[float]:
        """Embed using OpenAI text-embedding-3-large."""
        client = self._get_openai_client()
        try:
            response = await client.embeddings.create(
                model=settings.OPENAI_EMBEDDING_MODEL,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise

    async def _embed_gemini(self, text: str) -> List[float]:
        """Embed using Gemini embedding model."""
        genai = self._get_gemini_client()
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: genai.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    content=text,
                    task_type="retrieval_document",
                ),
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            raise

    async def _embed_groq(self, text: str) -> List[float]:
        """Embed using local sentence-transformers since Groq doesn't provide embeddings."""
        model = self._get_sentence_model()
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: model.encode(text).tolist()
            )
            return result
        except Exception as e:
            logger.error(f"Local sentence-transformers embedding error: {e}")
            raise


# Singleton instance
embedding_service = EmbeddingService()
