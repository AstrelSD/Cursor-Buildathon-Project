"""Fuse Gemini vision JSON with deterministic RGB signals for stabler underwriting scores."""

from __future__ import annotations

from app.models.schemas import VisionAnalysisResult
from app.vision.image_signals import ImageSignals

# Soft tolerance: small acreage mismatch should not dominate risk.
_ACREAGE_SOFT_RATIO = 0.20
_ACREAGE_HARD_RATIO = 0.45


def calibrate_vision_result(
    raw: VisionAnalysisResult,
    *,
    declared_acreage: float,
    signals: ImageSignals,
) -> VisionAnalysisResult:
    """Blend model output with ExG-based priors and declared-acreage bounds."""
    if raw.health_score <= 0 or raw.estimated_acreage <= 0:
        return raw

    exg_health = signals.vegetation_index * 100.0
    health = 0.72 * raw.health_score + 0.28 * exg_health
    if raw.disease_detected:
        health -= min(12.0, 4.0 * len(raw.detected_issues))
    health = _clamp(health, 0.0, 100.0)

    chlorophyll = 0.65 * raw.chlorophyll_index + 0.35 * signals.vegetation_index
    vegetation_index = 0.60 * raw.vegetation_index + 0.40 * signals.vegetation_index

    image_quality = 0.55 * raw.image_quality_score + 0.45 * signals.image_quality_score

    acreage = raw.estimated_acreage
    if raw.acreage_confidence < 0.45:
        # Low boundary confidence: shrink estimate toward declaration.
        acreage = 0.6 * declared_acreage + 0.4 * raw.estimated_acreage
    ratio = abs(acreage - declared_acreage) / max(declared_acreage, 0.1)
    if ratio > _ACREAGE_HARD_RATIO:
        acreage = declared_acreage * (1.0 + _ACREAGE_HARD_RATIO * (1 if acreage > declared_acreage else -1))
    elif ratio > _ACREAGE_SOFT_RATIO:
        pull = 0.35
        acreage = (1 - pull) * acreage + pull * declared_acreage

    crop_match = raw.crop_match_confidence
    if not signals.is_likely_field:
        image_quality = min(image_quality, 28.0)
        crop_match = min(crop_match, 0.35)

    return VisionAnalysisResult(
        estimated_acreage=round(max(acreage, 0.1), 2),
        chlorophyll_index=round(_clamp(chlorophyll, 0.0, 1.0), 3),
        disease_detected=raw.disease_detected,
        health_score=round(health, 1),
        image_quality_score=round(_clamp(image_quality, 0.0, 100.0), 1),
        crop_match_confidence=round(_clamp(crop_match, 0.0, 1.0), 3),
        canopy_cover_percent=round(_clamp(raw.canopy_cover_percent, 0.0, 100.0), 1),
        detected_issues=raw.detected_issues[:8],
        growth_stage=raw.growth_stage,
        acreage_confidence=round(_clamp(raw.acreage_confidence, 0.0, 1.0), 3),
        vegetation_index=round(_clamp(vegetation_index, 0.0, 1.0), 3),
    )


def acreage_variance_penalty(declared: float, estimated: float) -> float:
    """0–100 penalty with soft shoulder (research: declare vs remote-sense tolerance)."""
    if declared <= 0:
        return 100.0
    ratio = abs(declared - estimated) / declared
    if ratio <= _ACREAGE_SOFT_RATIO:
        return 0.0
    if ratio >= _ACREAGE_HARD_RATIO:
        return 100.0
    span = _ACREAGE_HARD_RATIO - _ACREAGE_SOFT_RATIO
    return round(((ratio - _ACREAGE_SOFT_RATIO) / span) * 100.0, 2)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
