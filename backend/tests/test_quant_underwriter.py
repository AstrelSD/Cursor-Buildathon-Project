"""Underwriter decision tests aligned with field-health gates."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.agents.quant_underwriter import QuantUnderwriterAgent
from app.models.schemas import MarketIntelligenceResult, VisionAnalysisResult


def _vision(**overrides: object) -> VisionAnalysisResult:
    base = {
        "estimated_acreage": 5.0,
        "chlorophyll_index": 0.7,
        "disease_detected": False,
        "health_score": 81.0,
        "image_quality_score": 28.0,
        "crop_match_confidence": 0.35,
        "canopy_cover_percent": 90.0,
        "vegetation_index": 0.67,
        "detected_issues": [],
    }
    base.update(overrides)
    return VisionAnalysisResult.model_validate(base)


class QuantUnderwriterDecisionTests(unittest.IsolatedAsyncioTestCase):
    async def test_rejects_low_field_health_even_when_risk_below_threshold(self) -> None:
        market = MarketIntelligenceResult(
            market_volatility_coefficient=0.2,
            weather_risk_score=12.0,
        )
        agent = QuantUnderwriterAgent()

        with patch.object(
            QuantUnderwriterAgent,
            "_execute_disbursement",
            new_callable=AsyncMock,
        ) as disburse:
            decision = await agent.decide(
                vision=_vision(),
                market=market,
                declared_acreage=5.0,
                requested_amount=475_000.0,
            )

        self.assertFalse(decision.approved)
        self.assertIsNotNone(decision.rejection_reason)
        assert decision.rejection_reason is not None
        self.assertIn("Field health review", decision.rejection_reason)
        self.assertLess(decision.calculated_risk_score, 45.0)
        disburse.assert_not_called()

    async def test_approves_when_field_health_and_risk_pass(self) -> None:
        market = MarketIntelligenceResult(
            market_volatility_coefficient=0.2,
            weather_risk_score=12.0,
        )
        agent = QuantUnderwriterAgent()

        with patch.object(
            QuantUnderwriterAgent,
            "_execute_disbursement",
            new_callable=AsyncMock,
            return_value=("REF-TEST", "[DISBURSED] mock"),
        ) as disburse:
            decision = await agent.decide(
                vision=_vision(image_quality_score=65.0, crop_match_confidence=0.72),
                market=market,
                declared_acreage=5.0,
                requested_amount=475_000.0,
            )

        self.assertTrue(decision.approved)
        disburse.assert_called_once()


if __name__ == "__main__":
    unittest.main()
