from __future__ import annotations

import logging
import uuid
from typing import Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings
from app.models.schemas import (
    MarketIntelligenceResult,
    UnderwriterDecision,
    VisionAnalysisResult,
)

logger = logging.getLogger(__name__)

GPT_MODEL = "gpt-4o"


class _UnderwriterNarrative(BaseModel):
    decision_logs: list[str] = Field(min_length=1)


class QuantUnderwriterAgent:
    def __init__(self) -> None:
        self._openai: Optional[AsyncOpenAI] = None
        if settings.openai_configured:
            api_key = settings.OPENAI_API_KEY.get_secret_value()  # type: ignore[union-attr]
            self._openai = AsyncOpenAI(api_key=api_key)

    @staticmethod
    def calculate_risk_score(
        vision: VisionAnalysisResult,
        market: MarketIntelligenceResult,
        declared_acreage: float,
    ) -> float:
        acreage_variance = min(
            abs(declared_acreage - vision.estimated_acreage) / declared_acreage,
            1.0,
        ) * 100
        score = (
            (0.5 * (100 - vision.health_score))
            + (0.3 * (market.market_volatility_coefficient * 100))
            + (0.2 * acreage_variance)
        )
        return round(min(max(score, 0.0), 100.0), 2)

    async def decide(
        self,
        vision: VisionAnalysisResult,
        market: MarketIntelligenceResult,
        declared_acreage: float,
        requested_amount: float,
    ) -> UnderwriterDecision:
        risk_score = self.calculate_risk_score(vision, market, declared_acreage)
        threshold = settings.RISK_REJECTION_THRESHOLD
        approved = risk_score <= threshold

        logs = await self._build_logs(
            vision=vision,
            market=market,
            declared_acreage=declared_acreage,
            requested_amount=requested_amount,
            risk_score=risk_score,
            threshold=threshold,
            approved=approved,
        )

        if not approved:
            return UnderwriterDecision(
                calculated_risk_score=risk_score,
                approved=False,
                rejection_reason=(
                    f"Risk score {risk_score:.2f} exceeds threshold {threshold:.2f}."
                ),
                decision_logs=logs,
            )

        transaction_reference = await self._simulate_disbursement(requested_amount)
        logs.append(
            f"[DISBURSED] Settlement simulation succeeded. Reference {transaction_reference}."
        )
        return UnderwriterDecision(
            calculated_risk_score=risk_score,
            approved=True,
            transaction_reference=transaction_reference,
            decision_logs=logs,
        )

    async def _build_logs(
        self,
        vision: VisionAnalysisResult,
        market: MarketIntelligenceResult,
        declared_acreage: float,
        requested_amount: float,
        risk_score: float,
        threshold: float,
        approved: bool,
    ) -> list[str]:
        base_logs = [
            "[VISION] Crop health matrix synthesized.",
            f"[MARKET] Volatility coefficient {market.market_volatility_coefficient:.2f}, "
            f"weather risk {market.weather_risk_score:.1f}.",
            f"[QUANT] Declared {declared_acreage:.2f} ac vs estimated "
            f"{vision.estimated_acreage:.2f} ac.",
            f"[QUANT] Immutable risk score {risk_score:.2f} "
            f"(threshold {threshold:.2f}).",
            f"[DECISION] {'APPROVED' if approved else 'REJECTED'} for LKR "
            f"{requested_amount:,.2f}.",
        ]

        if self._openai is None:
            return base_logs

        try:
            completion = await self._openai.beta.chat.completions.parse(
                model=GPT_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are QuantUnderwriterAgent. Produce 2-4 concise underwriting "
                            "log lines. Do not change numeric risk values."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"health_score={vision.health_score}, "
                            f"market_volatility={market.market_volatility_coefficient}, "
                            f"risk_score={risk_score}, approved={approved}"
                        ),
                    },
                ],
                response_format=_UnderwriterNarrative,
                temperature=0.2,
            )
            narrative = completion.choices[0].message.parsed
            if narrative and narrative.decision_logs:
                return base_logs + narrative.decision_logs
        except Exception:
            logger.exception("GPT-4o narrative generation failed; using deterministic logs.")

        return base_logs

    @staticmethod
    async def _simulate_disbursement(requested_amount: float) -> str:
        reference = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        logger.info(
            "Simulated disbursement of LKR %s with reference %s",
            f"{requested_amount:,.2f}",
            reference,
        )
        return reference
