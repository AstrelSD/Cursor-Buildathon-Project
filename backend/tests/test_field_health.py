"""Unit tests for field-health assessment and vision gates."""

from __future__ import annotations

import unittest

from app.models.schemas import VisionAnalysisResult
from app.vision.field_health import (
    FieldHealthBand,
    FieldHealthValidationError,
    assess_field_health,
    assess_field_health_from_vision,
    field_health_rejection_reason,
    validate_vision_metrics,
)


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


class FieldHealthAssessmentTests(unittest.TestCase):
    def test_low_band_for_weak_photo_and_crop_match(self) -> None:
        assessment = assess_field_health_from_vision(_vision())
        self.assertEqual(assessment.band, FieldHealthBand.LOW)
        self.assertIn("photo quality", assessment.triggers[0])

    def test_medium_when_only_moderate_uncertainty(self) -> None:
        assessment = assess_field_health_from_vision(
            _vision(image_quality_score=55.0, crop_match_confidence=0.55),
        )
        self.assertEqual(assessment.band, FieldHealthBand.MEDIUM)

    def test_high_band_when_all_signals_strong(self) -> None:
        assessment = assess_field_health_from_vision(
            _vision(
                health_score=85.0,
                image_quality_score=70.0,
                crop_match_confidence=0.8,
            ),
        )
        self.assertEqual(assessment.band, FieldHealthBand.HIGH)

    def test_risk_score_can_trigger_low_band(self) -> None:
        assessment = assess_field_health(
            health_score=80.0,
            disease_detected=False,
            image_quality_score=70.0,
            crop_match_confidence=0.8,
            calculated_risk_score=60.0,
        )
        self.assertEqual(assessment.band, FieldHealthBand.LOW)


class VisionValidationTests(unittest.TestCase):
    def test_rejects_example_that_ui_labels_low(self) -> None:
        with self.assertRaises(FieldHealthValidationError) as ctx:
            validate_vision_metrics(_vision())
        self.assertIn("photo quality", str(ctx.exception).lower())

    def test_rejection_reason_is_actionable(self) -> None:
        assessment = assess_field_health_from_vision(_vision())
        reason = field_health_rejection_reason(assessment)
        self.assertIn("Retake", reason)


if __name__ == "__main__":
    unittest.main()
