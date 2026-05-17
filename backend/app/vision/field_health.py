"""Canonical field-health rules for vision gates and underwriting.

Keep thresholds in sync with frontend/lib/field-health-thresholds.ts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.models.schemas import VisionAnalysisResult

# --- Thresholds (mirrored in frontend/lib/field-health-thresholds.ts) ---

MIN_IMAGE_QUALITY_SCORE = 40.0
MIN_CROP_MATCH_CONFIDENCE = 0.40
MIN_HEALTH_SCORE = 45.0
HIGH_HEALTH_SCORE = 72.0
HIGH_IMAGE_QUALITY_SCORE = 58.0
HIGH_CROP_MATCH_CONFIDENCE = 0.65
RISK_SCORE_LOW_BAND = 55.0
RISK_SCORE_HIGH_BAND = 38.0


class FieldHealthBand(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class FieldHealthAssessment:
    band: FieldHealthBand
    label: str
    summary: str
    triggers: tuple[str, ...]


def assess_field_health(
    *,
    health_score: float,
    disease_detected: bool,
    image_quality_score: Optional[float] = None,
    crop_match_confidence: Optional[float] = None,
    detected_issues: Optional[list[str]] = None,
    calculated_risk_score: Optional[float] = None,
) -> FieldHealthAssessment:
    """Classify field imagery into high / medium / low confidence."""
    issues = detected_issues or []

    low_triggers: list[str] = []
    if health_score < MIN_HEALTH_SCORE:
        low_triggers.append(f"health score below {MIN_HEALTH_SCORE:.0f}")
    if disease_detected:
        low_triggers.append("disease or stress flagged")
    if image_quality_score is not None and image_quality_score < MIN_IMAGE_QUALITY_SCORE:
        low_triggers.append(
            f"photo quality below {MIN_IMAGE_QUALITY_SCORE:.0f}/100",
        )
    if crop_match_confidence is not None and crop_match_confidence < MIN_CROP_MATCH_CONFIDENCE:
        low_triggers.append(
            f"crop match below {MIN_CROP_MATCH_CONFIDENCE * 100:.0f}%",
        )
    if calculated_risk_score is not None and calculated_risk_score > RISK_SCORE_LOW_BAND:
        low_triggers.append(f"risk score above {RISK_SCORE_LOW_BAND:.0f}")

    high_ok = (
        health_score >= HIGH_HEALTH_SCORE
        and not disease_detected
        and len(issues) == 0
        and (image_quality_score is None or image_quality_score >= HIGH_IMAGE_QUALITY_SCORE)
        and (
            crop_match_confidence is None
            or crop_match_confidence >= HIGH_CROP_MATCH_CONFIDENCE
        )
        and (
            calculated_risk_score is None
            or calculated_risk_score <= RISK_SCORE_HIGH_BAND
        )
    )

    if low_triggers:
        band = FieldHealthBand.LOW
        label = "Low confidence"
        summary = (
            "Field health or photo quality does not meet underwriting standards. "
            "Submit a clear daylight photo of the declared crop before reapplying."
        )
    elif high_ok:
        band = FieldHealthBand.HIGH
        label = "High confidence"
        summary = "Field imagery shows strong canopy vigor with no major stress signals."
    else:
        band = FieldHealthBand.MEDIUM
        label = "Medium confidence"
        summary = (
            "Field looks workable; some stress or uncertainty was detected — "
            "underwriting will weigh these signals in the risk score."
        )

    return FieldHealthAssessment(
        band=band,
        label=label,
        summary=summary,
        triggers=tuple(low_triggers),
    )


def assess_field_health_from_vision(
    vision: VisionAnalysisResult,
    calculated_risk_score: Optional[float] = None,
) -> FieldHealthAssessment:
    return assess_field_health(
        health_score=vision.health_score,
        disease_detected=vision.disease_detected,
        image_quality_score=vision.image_quality_score,
        crop_match_confidence=vision.crop_match_confidence,
        detected_issues=vision.detected_issues,
        calculated_risk_score=calculated_risk_score,
    )


def field_health_rejection_reason(assessment: FieldHealthAssessment) -> str:
    detail = "; ".join(assessment.triggers) if assessment.triggers else "signals below minimum"
    return (
        "Evaluation failed: Field health review did not pass underwriting "
        f"({detail}). Retake a clear daylight photo showing the full declared crop."
    )


class FieldHealthValidationError(Exception):
    """Raised when crop evidence fails shared field-health gates."""


def validate_vision_metrics(result: VisionAnalysisResult) -> None:
    """Hard gates before underwriting; uses the same thresholds as the low band."""
    if result.health_score <= 0 or result.estimated_acreage <= 0:
        raise FieldHealthValidationError(
            "Evaluation failed: Crop imagery unreadable.",
        )

    if result.image_quality_score < MIN_IMAGE_QUALITY_SCORE:
        raise FieldHealthValidationError(
            "Evaluation failed: Image too blurry, dark, or low resolution. "
            f"Photo quality must be at least {MIN_IMAGE_QUALITY_SCORE:.0f}/100. "
            "Retake the photo in daylight with the full field visible.",
        )

    if result.crop_match_confidence < MIN_CROP_MATCH_CONFIDENCE:
        raise FieldHealthValidationError(
            "Evaluation failed: Photo does not sufficiently match the declared crop type. "
            f"Crop match must be at least {MIN_CROP_MATCH_CONFIDENCE * 100:.0f}%.",
        )

    assessment = assess_field_health_from_vision(result)
    if assessment.band == FieldHealthBand.LOW:
        raise FieldHealthValidationError(field_health_rejection_reason(assessment))
