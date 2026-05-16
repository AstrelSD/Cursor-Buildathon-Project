from __future__ import annotations

import logging

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSIONS = 1536
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
# Try embedding-2 variants first, then 001. (Not gemini-embedding-002 — invalid ID.)
GEMINI_EMBEDDING_FALLBACKS = (
    "gemini-embedding-2-preview",
    "gemini-embedding-001",
)


def build_market_query_text(crop_type: str, district: str) -> str:
    return (
        f"Agronomic micro-credit risk context for {crop_type} cultivation "
        f"in {district} district, Sri Lanka. Include localized market volatility "
        f"and weather exposure."
    )


def _gemini_embedding_models() -> list[str]:
    models = [settings.GEMINI_EMBEDDING_MODEL, *GEMINI_EMBEDDING_FALLBACKS]
    seen: set[str] = set()
    ordered: list[str] = []
    for model in models:
        if model and model not in seen:
            seen.add(model)
            ordered.append(model)
    return ordered


async def _embed_with_gemini(
    text: str,
    *,
    gemini_task_type: str,
) -> list[float]:
    client = genai.Client(
        api_key=settings.GOOGLE_GENAI_API_KEY.get_secret_value()  # type: ignore[union-attr]
    )
    last_error: Exception | None = None

    for model in _gemini_embedding_models():
        try:
            response = await client.aio.models.embed_content(
                model=model,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=gemini_task_type,
                    output_dimensionality=EMBEDDING_DIMENSIONS,
                ),
            )
            if not response.embeddings:
                raise RuntimeError("Gemini returned no embeddings.")
            logger.debug("Embedding created with model=%s", model)
            return list(response.embeddings[0].values)
        except ClientError as exc:
            last_error = exc
            logger.warning("Gemini embedding failed for model=%s: %s", model, exc)
            continue

    raise RuntimeError(
        "Gemini embedding failed for all models. "
        "Try GEMINI_EMBEDDING_MODEL=gemini-embedding-2 or gemini-embedding-2-preview."
    ) from last_error


async def embed_text(
    text: str,
    *,
    gemini_task_type: str = "RETRIEVAL_QUERY",
) -> list[float]:
    """Create a 1536-dim embedding using OpenAI or Gemini (Gemini-only is supported)."""
    if settings.openai_configured:
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())  # type: ignore[union-attr]
        response = await client.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=text,
            dimensions=EMBEDDING_DIMENSIONS,
        )
        return response.data[0].embedding

    if settings.google_genai_configured:
        return await _embed_with_gemini(text, gemini_task_type=gemini_task_type)

    raise RuntimeError(
        "No embedding provider configured. Set GOOGLE_GENAI_API_KEY or OPENAI_API_KEY."
    )
