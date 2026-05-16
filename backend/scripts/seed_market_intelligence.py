#!/usr/bin/env python3
"""
Seed public.market_intelligence for every supported crop × Sri Lanka district.

Uses Gemini embedding-2 (see GEMINI_EMBEDDING_MODEL) when only GOOGLE_GENAI_API_KEY is set.
Expect ~182 embedding API calls (7 crops × 26 districts); may take several minutes.

Run from project root after expanding profile districts:
  docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm api \\
    python scripts/seed_market_intelligence.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.database import close_supabase, get_supabase, init_supabase
from app.embeddings import build_market_query_text, embed_text
from app.market_intelligence_seed import build_seed_rows

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("seed_market_intelligence")

# Pause between embedding calls to reduce Gemini rate-limit errors.
EMBED_DELAY_SEC = 0.15


async def main() -> None:
    if not settings.supabase_configured:
        raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in backend/.env")

    if not settings.google_genai_configured and not settings.openai_configured:
        raise SystemExit("Set GOOGLE_GENAI_API_KEY or OPENAI_API_KEY in backend/.env")

    rows = build_seed_rows()
    logger.info("Seeding %d crop/district market_intelligence rows...", len(rows))

    await init_supabase()
    client = get_supabase()

    logger.info("Clearing existing market_intelligence rows...")
    await client.table("market_intelligence").delete().neq(
        "id", "00000000-0000-0000-0000-000000000000"
    ).execute()

    for index, row in enumerate(rows, start=1):
        crop = str(row["crop_type"])
        district = str(row["district"])
        query_text = build_market_query_text(crop, district)
        logger.info("[%s/%s] Embedding %s / %s ...", index, len(rows), crop, district)
        embedding = await embed_text(
            query_text,
            gemini_task_type="RETRIEVAL_DOCUMENT",
        )

        payload = {**row, "embedding": embedding, "metadata": {"source": "seed_script_v2"}}
        await client.table("market_intelligence").insert(payload).execute()

        if index < len(rows) and EMBED_DELAY_SEC > 0:
            await asyncio.sleep(EMBED_DELAY_SEC)

    await close_supabase()
    logger.info("Done. Seeded %d market_intelligence rows.", len(rows))


if __name__ == "__main__":
    asyncio.run(main())
