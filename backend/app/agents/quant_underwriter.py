from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings
from app.services.seylan_api_service import SeylanApiError, disburse_loan_amount
from app.models.schemas import (
    MarketIntelligenceResult,
    UnderwriterDecision,
    VisionAnalysisResult,
)
from app.vision.calibration import acreage_variance_penalty
from app.vision.field_health import (
    FieldHealthBand,
    assess_field_health_from_vision,
    field_health_rejection_reason,
)

logger = logging.getLogger(__name__)

GPT_MODEL = "gpt-4o"

# Weights tuned for multimodal ag credit (vision + market + declaration alignment).
_WEIGHT_HEALTH = 0.28
_WEIGHT_DISEASE = 0.13
_WEIGHT_MARKET = 0.18
_WEIGHT_WEATHER = 0.12
_WEIGHT_ACREAGE = 0.12
_WEIGHT_IMAGE = 0.10
_WEIGHT_CROP_MATCH = 0.07


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
        health_component = 100.0 - vision.health_score

        disease_component = 0.0
        if vision.disease_detected:
            disease_component = min(
                100.0,
                55.0 + 12.0 * len(vision.detected_issues),
            )

        market_component = market.market_volatility_coefficient * 100.0
        weather_component = min(market.weather_risk_score / 28.0, 1.0) * 100.0
        acreage_component = acreage_variance_penalty(
            declared_acreage,
            vision.estimated_acreage,
        )
        image_component = 100.0 - vision.image_quality_score
        crop_match_component = (1.0 - vision.crop_match_confidence) * 100.0

        score = (
            _WEIGHT_HEALTH * health_component
            + _WEIGHT_DISEASE * disease_component
            + _WEIGHT_MARKET * market_component
            + _WEIGHT_WEATHER * weather_component
            + _WEIGHT_ACREAGE * acreage_component
            + _WEIGHT_IMAGE * image_component
            + _WEIGHT_CROP_MATCH * crop_match_component
        )
        return round(min(max(score, 0.0), 100.0), 2)

    async def decide(
        self,
        vision: VisionAnalysisResult,
        market: MarketIntelligenceResult,
        declared_acreage: float,
        requested_amount: float,
        *,
        loan_id: Optional[UUID] = None,
    ) -> UnderwriterDecision:
        risk_score = self.calculate_risk_score(vision, market, declared_acreage)
        threshold = settings.RISK_REJECTION_THRESHOLD
        field_health = assess_field_health_from_vision(vision, risk_score)
        risk_acceptable = risk_score <= threshold
        field_health_acceptable = field_health.band != FieldHealthBand.LOW
        approved = risk_acceptable and field_health_acceptable

        logs = await self._build_logs(
            vision=vision,
            market=market,
            declared_acreage=declared_acreage,
            requested_amount=requested_amount,
            risk_score=risk_score,
            threshold=threshold,
            approved=approved,
            field_health_band=field_health.band.value,
        )

        if not field_health_acceptable:
            return UnderwriterDecision(
                calculated_risk_score=risk_score,
                approved=False,
                rejection_reason=field_health_rejection_reason(field_health),
                decision_logs=logs,
            )

        if not risk_acceptable:
            return UnderwriterDecision(
                calculated_risk_score=risk_score,
                approved=False,
                rejection_reason=(
                    f"Risk score {risk_score:.2f} exceeds threshold {threshold:.2f}."
                ),
                decision_logs=logs,
            )

        transaction_reference, disbursement_log = await self._execute_disbursement(
            requested_amount,
            loan_id=loan_id,
        )
        logs.append(disbursement_log)
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
        field_health_band: str,
    ) -> list[str]:
        issues = ", ".join(vision.detected_issues) if vision.detected_issues else "none"
        base_logs = [
            "[VISION] Crop health matrix synthesized.",
            f"[FIELD_HEALTH] Confidence band={field_health_band}.",
            (
                f"[VISION] health={vision.health_score:.1f}, canopy={vision.canopy_cover_percent:.0f}%, "
                f"ExG={vision.vegetation_index:.2f}, quality={vision.image_quality_score:.0f}, "
                f"crop_match={vision.crop_match_confidence:.2f}, stage={vision.growth_stage}."
            ),
            f"[VISION] Issues: {issues}; disease_flag={vision.disease_detected}.",
            (
                f"[MARKET] Volatility {market.market_volatility_coefficient:.2f}, "
                f"weather risk {market.weather_risk_score:.1f}."
            ),
            (
                f"[QUANT] Declared {declared_acreage:.2f} ac vs estimated "
                f"{vision.estimated_acreage:.2f} ac (confidence {vision.acreage_confidence:.2f})."
            ),
            (
                f"[QUANT] Immutable risk score {risk_score:.2f} "
                f"(threshold {threshold:.2f})."
            ),
            f"[DECISION] {'APPROVED' if approved else 'REJECTED'} for LKR {requested_amount:,.2f}.",
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
                            "log lines referencing vision pathology, canopy, and market weather. "
                            "Do not change numeric risk values."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"health_score={vision.health_score}, "
                            f"canopy={vision.canopy_cover_percent}, "
                            f"issues={issues}, "
                            f"disease={vision.disease_detected}, "
                            f"market_volatility={market.market_volatility_coefficient}, "
                            f"weather_risk={market.weather_risk_score}, "
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
    async def _execute_disbursement(
        requested_amount: float,
        *,
        loan_id: Optional[UUID] = None,
    ) -> tuple[str, str]:
        try:
            reference, mode = await disburse_loan_amount(
                requested_amount,
                loan_id=str(loan_id) if loan_id else None,
            )
        except SeylanApiError:
            logger.exception("Seylan sandbox disbursement failed")
            raise

        if mode == "mock":
            return (
                reference,
                (
                    f"[DISBURSED] Mock CEFTS to {settings.SEYLAN_CEFTS_DESTINATION_ACCOUNT}"
                    f"@{settings.SEYLAN_CEFTS_DESTINATION_BANK_CODE} "
                    f"(live Posting pending). Reference {reference}."
                ),
            )

        logger.info(
            "CEFTS disbursement of LKR %s succeeded. Reference %s",
            f"{requested_amount:,.2f}",
            reference,
        )
        return (
            reference,
            f"[DISBURSED] CEFTS transfer via Seylan sandbox succeeded. Reference {reference}.",
        )
