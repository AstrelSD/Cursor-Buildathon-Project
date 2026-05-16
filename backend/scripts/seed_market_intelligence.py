#!/usr/bin/env python3
"""
Seed public.market_intelligence with Sri Lanka district/crop reference rows.

Uses Gemini embedding-2 (see GEMINI_EMBEDDING_MODEL) when only GOOGLE_GENAI_API_KEY is set.

Run from project root:
  docker compose run --rm api python scripts/seed_market_intelligence.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Allow `from app...` when executed as scripts/seed_market_intelligence.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.database import close_supabase, get_supabase, init_supabase
from app.embeddings import build_market_query_text, embed_text

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("seed_market_intelligence")

SEED_ROWS = [
    {
        "crop_type": "Paddy",
        "district": "Anuradhapura",
        "base_yield_index": 82.50,
        "market_volatility_coefficient": 0.35,
        "weather_risk_score": 12.50,
    },
    {
        "crop_type": "Paddy",
        "district": "Polonnaruwa",
        "base_yield_index": 80.10,
        "market_volatility_coefficient": 0.42,
        "weather_risk_score": 15.20,
    },
    {
        "crop_type": "Paddy",
        "district": "Ampara",
        "base_yield_index": 78.40,
        "market_volatility_coefficient": 0.38,
        "weather_risk_score": 18.00,
    },
    {
        "crop_type": "Paddy",
        "district": "Kurunegala",
        "base_yield_index": 81.20,
        "market_volatility_coefficient": 0.31,
        "weather_risk_score": 11.80,
    },
    {
        "crop_type": "Paddy",
        "district": "Nuwaraliya",
        "base_yield_index": 76.90,
        "market_volatility_coefficient": 0.48,
        "weather_risk_score": 22.40,
    },
    {
        "crop_type": "Tea",
        "district": "Nuwaraliya",
        "base_yield_index": 88.00,
        "market_volatility_coefficient": 0.29,
        "weather_risk_score": 9.50,
    },
    {
        "crop_type": "Tea",
        "district": "Kurunegala",
        "base_yield_index": 74.50,
        "market_volatility_coefficient": 0.33,
        "weather_risk_score": 14.10,
    },
    {
        "crop_type": "Maize",
        "district": "Ampara",
        "base_yield_index": 79.30,
        "market_volatility_coefficient": 0.40,
        "weather_risk_score": 16.70,
    },
]


async def main() -> None:
    if not settings.supabase_configured:
        raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in backend/.env")

    if not settings.google_genai_configured and not settings.openai_configured:
        raise SystemExit("Set GOOGLE_GENAI_API_KEY or OPENAI_API_KEY in backend/.env")

    await init_supabase()
    client = get_supabase()

    logger.info("Clearing existing market_intelligence rows...")
    await client.table("market_intelligence").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    for row in SEED_ROWS:
        query_text = build_market_query_text(row["crop_type"], row["district"])
        logger.info("Embedding %s / %s ...", row["crop_type"], row["district"])
        embedding = await embed_text(
            query_text,
            gemini_task_type="RETRIEVAL_DOCUMENT",
        )

        payload = {**row, "embedding": embedding, "metadata": {"source": "seed_script"}}
        await client.table("market_intelligence").insert(payload).execute()
        logger.info("Inserted %s / %s", row["crop_type"], row["district"])

    await close_supabase()
    logger.info("Done. Seeded %d market_intelligence rows.", len(SEED_ROWS))


if __name__ == "__main__":
    asyncio.run(main())
