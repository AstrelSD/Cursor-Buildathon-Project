from __future__ import annotations

import logging

from app.database import get_supabase
from app.embeddings import build_market_query_text, embed_text
from app.models.schemas import MarketIntelligenceResult

logger = logging.getLogger(__name__)

DEFAULT_MARKET = MarketIntelligenceResult(
    market_volatility_coefficient=0.5,
    weather_risk_score=25.0,
)


def _row_to_result(row: dict[str, object]) -> MarketIntelligenceResult:
    return MarketIntelligenceResult(
        market_volatility_coefficient=float(row["market_volatility_coefficient"]),
        weather_risk_score=float(row["weather_risk_score"]),
    )


async def _lookup_by_vector(query_embedding: list[float]) -> MarketIntelligenceResult | None:
    client = get_supabase()
    response = await client.rpc(
        "match_market_intelligence",
        {
            "query_embedding": query_embedding,
            "match_count": 1,
        },
    ).execute()

    rows = response.data if response is not None else None
    if not rows:
        return None
    logger.info(
        "Market RAG vector match similarity=%.4f",
        float(rows[0].get("similarity", 0)),
    )
    return _row_to_result(rows[0])


async def _lookup_by_crop_and_district(
    crop_type: str,
    district: str,
) -> MarketIntelligenceResult | None:
    client = get_supabase()
    response = await (
        client.table("market_intelligence")
        .select("market_volatility_coefficient, weather_risk_score")
        .eq("crop_type", crop_type)
        .eq("district", district)
        .limit(1)
        .execute()
    )
    rows = response.data if response is not None else None
    if not rows:
        return None
    logger.info("Market RAG exact match for crop=%s district=%s", crop_type, district)
    return _row_to_result(rows[0])


class MarketIntelligenceRagAgent:
    async def retrieve(
        self,
        crop_type: str,
        district: str,
    ) -> MarketIntelligenceResult:
        query_text = build_market_query_text(crop_type, district)
        query_embedding = await embed_text(query_text)

        vector_match = await _lookup_by_vector(query_embedding)
        if vector_match is not None:
            return vector_match

        exact_match = await _lookup_by_crop_and_district(crop_type, district)
        if exact_match is not None:
            return exact_match

        logger.warning(
            "No market_intelligence data for crop=%s district=%s — using defaults. "
            "Re-run: docker compose run --rm api python scripts/seed_market_intelligence.py",
            crop_type,
            district,
        )
        return DEFAULT_MARKET
