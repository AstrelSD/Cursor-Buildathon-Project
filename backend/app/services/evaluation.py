from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from app.agents.market_rag import MarketIntelligenceRagAgent
from app.agents.quant_underwriter import QuantUnderwriterAgent
from app.agents.vision_agronomist import (
    VisionAgronomistAgent,
    VisionAnalysisError,
    VisionQuotaError,
)
from app.config import settings
from app.database import get_supabase
from app.models.schemas import LoanRecord
from app.services.storage import guess_mime_type, resolve_storage_location

logger = logging.getLogger(__name__)

VISION_REJECTION_REASON = "Evaluation failed: Crop imagery unreadable."


async def _fetch_loan(loan_id: UUID) -> LoanRecord:
    client = get_supabase()
    response = await (
        client.table("loans")
        .select("*, profiles(district)")
        .eq("id", str(loan_id))
        .limit(1)
        .execute()
    )
    if response is None or not response.data:
        raise ValueError(f"Loan {loan_id} not found.")
    return LoanRecord.from_row(response.data[0])


async def _update_loan(loan_id: UUID, payload: dict[str, object]) -> None:
    client = get_supabase()
    await client.table("loans").update(payload).eq("id", str(loan_id)).execute()


async def _download_evidence(evidence_url: str) -> tuple[bytes, str]:
    bucket, object_path = resolve_storage_location(evidence_url)
    client = get_supabase()
    data = await client.storage.from_(bucket).download(object_path)
    if isinstance(data, bytes):
        return data, guess_mime_type(object_path)
    return bytes(data), guess_mime_type(object_path)


async def run_evaluation_pipeline(loan_id: UUID) -> None:
    logger.info("Starting evaluation pipeline for loan %s", loan_id)

    try:
        loan = await _fetch_loan(loan_id)
    except Exception:
        logger.exception("Failed to load loan %s", loan_id)
        return

    if not loan.multimodal_evidence_url:
        await _update_loan(
            loan_id,
            {
                "status": "rejected",
                "rejection_reason": VISION_REJECTION_REASON,
            },
        )
        return

    if not loan.district:
        await _update_loan(
            loan_id,
            {
                "status": "rejected",
                "rejection_reason": "Evaluation failed: Farmer district profile missing.",
            },
        )
        return

    await _update_loan(loan_id, {"status": "analyzing"})

    vision_agent = VisionAgronomistAgent()
    market_agent = MarketIntelligenceRagAgent()

    try:
        image_bytes, mime_type = await _download_evidence(loan.multimodal_evidence_url)
    except Exception:
        logger.exception("Evidence download failed for loan %s", loan_id)
        await _update_loan(
            loan_id,
            {"status": "rejected", "rejection_reason": VISION_REJECTION_REASON},
        )
        return

    vision_out, market_out = await asyncio.gather(
        vision_agent.analyze(
            image_bytes=image_bytes,
            mime_type=mime_type,
            declared_acreage=loan.declared_acreage,
        ),
        market_agent.retrieve(crop_type=loan.crop_type, district=loan.district),
        return_exceptions=True,
    )

    if isinstance(vision_out, VisionQuotaError):
        await _update_loan(
            loan_id,
            {"status": "rejected", "rejection_reason": vision_out.message},
        )
        return

    if isinstance(vision_out, VisionAnalysisError):
        await _update_loan(
            loan_id,
            {
                "status": "rejected",
                "rejection_reason": vision_out.message or VISION_REJECTION_REASON,
            },
        )
        return

    if isinstance(vision_out, Exception):
        logger.exception("Vision agent failed for loan %s", loan_id, exc_info=vision_out)
        await _update_loan(
            loan_id,
            {"status": "rejected", "rejection_reason": VISION_REJECTION_REASON},
        )
        return

    if isinstance(market_out, Exception):
        logger.exception("Market RAG agent failed for loan %s", loan_id, exc_info=market_out)
        await _update_loan(
            loan_id,
            {
                "status": "rejected",
                "rejection_reason": "Evaluation failed: Market intelligence unavailable.",
            },
        )
        return

    vision_result = vision_out
    market_result = market_out

    await _update_loan(
        loan_id,
        {
            "ai_verified_acreage": vision_result.estimated_acreage,
            "crop_health_matrix": {
                "chlorophyll_index": vision_result.chlorophyll_index,
                "anomaly_flag": vision_result.disease_detected,
                "classification": "diseased" if vision_result.disease_detected else "healthy",
                "health_score": vision_result.health_score,
            },
            "market_volatility_index": market_result.market_volatility_coefficient,
        },
    )

    await _update_loan(loan_id, {"status": "underwriting"})

    underwriter = QuantUnderwriterAgent()
    decision = await underwriter.decide(
        vision=vision_result,
        market=market_result,
        declared_acreage=loan.declared_acreage,
        requested_amount=loan.requested_amount,
    )

    if not decision.approved:
        await _update_loan(
            loan_id,
            {
                "status": "rejected",
                "calculated_risk_score": decision.calculated_risk_score,
                "rejection_reason": decision.rejection_reason,
            },
        )
        logger.info("Loan %s rejected with risk %.2f", loan_id, decision.calculated_risk_score)
        return

    await _update_loan(
        loan_id,
        {
            "status": "approved",
            "calculated_risk_score": decision.calculated_risk_score,
            "rejection_reason": None,
        },
    )

    await _update_loan(
        loan_id,
        {
            "status": "disbursed",
            "transaction_reference": decision.transaction_reference,
        },
    )
    logger.info(
        "Loan %s disbursed. Risk=%.2f ref=%s",
        loan_id,
        decision.calculated_risk_score,
        decision.transaction_reference,
    )
