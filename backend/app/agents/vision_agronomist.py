from __future__ import annotations

import json
import logging
import re
from typing import Optional

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from app.config import settings
from app.models.schemas import VisionAnalysisResult
from app.vision.calibration import calibrate_vision_result
from app.vision.image_signals import (
    ImageSignals,
    analyze_image_bytes,
    prepare_image_for_vision,
)
from app.vision.prompts import build_vision_system_prompt, build_vision_user_prompt

logger = logging.getLogger(__name__)

MIN_IMAGE_QUALITY = 28.0


class VisionAnalysisError(Exception):
    """Raised when crop evidence cannot be analyzed."""

    def __init__(self, message: str = "Evaluation failed: Crop imagery unreadable.") -> None:
        super().__init__(message)
        self.message = message


class VisionQuotaError(VisionAnalysisError):
    """Raised when Gemini vision quota/rate limits are exceeded."""

    def __init__(self) -> None:
        super().__init__(
            "Evaluation failed: Gemini API quota exceeded. "
            "Wait ~1 minute and retry, set GEMINI_VISION_MODEL=gemini-1.5-flash in .env, "
            "or enable MOCK_VISION_ON_FAILURE=true for demo mode."
        )


def _extract_json_payload(text: str) -> str:
    stripped = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", stripped)
    if fence_match:
        return fence_match.group(1).strip()
    return stripped


def _vision_model_candidates() -> list[str]:
    models = [settings.GEMINI_VISION_MODEL]
    models.extend(
        m.strip()
        for m in settings.GEMINI_VISION_FALLBACK_MODELS.split(",")
        if m.strip()
    )
    seen: set[str] = set()
    ordered: list[str] = []
    for model in models:
        if model not in seen:
            seen.add(model)
            ordered.append(model)
    return ordered


def _mock_vision_result(
    declared_acreage: float,
    signals: ImageSignals,
) -> VisionAnalysisResult:
    """Deterministic fallback aligned with RGB pre-analysis."""
    health = round(52.0 + 40.0 * signals.vegetation_index, 1)
    return VisionAnalysisResult(
        estimated_acreage=round(declared_acreage * 0.97, 2),
        chlorophyll_index=round(signals.vegetation_index * 0.95, 3),
        disease_detected=False,
        health_score=health,
        image_quality_score=signals.image_quality_score,
        crop_match_confidence=0.78 if signals.is_likely_field else 0.4,
        canopy_cover_percent=round(45.0 + 35.0 * signals.vegetation_index, 1),
        detected_issues=[],
        growth_stage="vegetative",
        acreage_confidence=0.55,
        vegetation_index=signals.vegetation_index,
    )


class VisionAgronomistAgent:
    def __init__(self) -> None:
        if not settings.google_genai_configured:
            raise RuntimeError("GOOGLE_GENAI_API_KEY is not configured.")
        api_key = settings.GOOGLE_GENAI_API_KEY.get_secret_value()  # type: ignore[union-attr]
        self._client = genai.Client(api_key=api_key)

    async def analyze(
        self,
        image_bytes: bytes,
        mime_type: str,
        declared_acreage: float,
        crop_type: str,
        district: str | None = None,
    ) -> VisionAnalysisResult:
        if not image_bytes:
            raise VisionAnalysisError()

        prepared_bytes, prepared_mime = prepare_image_for_vision(image_bytes, mime_type)
        signals = analyze_image_bytes(prepared_bytes)

        if not signals.is_likely_field and signals.image_quality_score < 32.0:
            raise VisionAnalysisError(
                "Evaluation failed: Photo does not appear to show a crop field. "
                "Upload a clear outdoor field image in daylight."
            )

        prompt = build_vision_user_prompt(
            crop_type=crop_type,
            district=district,
            declared_acreage=declared_acreage,
            signals=signals,
        )
        contents = [
            types.Part.from_bytes(data=prepared_bytes, mime_type=prepared_mime),
            types.Part.from_text(text=prompt),
        ]
        config = types.GenerateContentConfig(
            system_instruction=build_vision_system_prompt(),
            temperature=0.15,
            response_mime_type="application/json",
        )

        last_error: Optional[Exception] = None
        quota_hit = False

        for model_id in _vision_model_candidates():
            try:
                response = await self._client.aio.models.generate_content(
                    model=model_id,
                    contents=contents,
                    config=config,
                )
                raw = self._parse_response(response.text, model_id)
                calibrated = calibrate_vision_result(
                    raw,
                    declared_acreage=declared_acreage,
                    signals=signals,
                )
                self._validate_for_underwriting(calibrated)
                logger.info(
                    "Vision analysis via %s health=%.1f quality=%.1f crop_match=%.2f issues=%s",
                    model_id,
                    calibrated.health_score,
                    calibrated.image_quality_score,
                    calibrated.crop_match_confidence,
                    calibrated.detected_issues,
                )
                return calibrated
            except VisionAnalysisError:
                raise
            except ClientError as exc:
                last_error = exc
                if exc.status_code == 429:
                    quota_hit = True
                    logger.warning("Gemini vision quota exceeded for model=%s", model_id)
                    continue
                logger.exception("Gemini vision client error for model=%s", model_id)
                break
            except Exception as exc:
                last_error = exc
                logger.exception("Gemini vision request failed for model=%s", model_id)
                continue

        if settings.MOCK_VISION_ON_FAILURE:
            logger.warning("Using MOCK_VISION_ON_FAILURE for crop=%s", crop_type)
            mock = _mock_vision_result(declared_acreage, signals)
            return calibrate_vision_result(
                mock,
                declared_acreage=declared_acreage,
                signals=signals,
            )

        if quota_hit:
            raise VisionQuotaError() from last_error

        raise VisionAnalysisError() from last_error

    @staticmethod
    def _validate_for_underwriting(result: VisionAnalysisResult) -> None:
        if result.health_score <= 0 or result.estimated_acreage <= 0:
            raise VisionAnalysisError()
        if result.image_quality_score < MIN_IMAGE_QUALITY:
            raise VisionAnalysisError(
                "Evaluation failed: Image too blurry, dark, or low resolution. "
                "Retake the photo in daylight with the full field visible."
            )
        if result.crop_match_confidence < 0.25:
            raise VisionAnalysisError(
                "Evaluation failed: Photo does not match the declared crop type."
            )

    @staticmethod
    def _parse_response(text: Optional[str], model_id: str) -> VisionAnalysisResult:
        if not text:
            raise VisionAnalysisError()

        try:
            payload = json.loads(_extract_json_payload(text))
            if isinstance(payload.get("detected_issues"), str):
                payload["detected_issues"] = [payload["detected_issues"]]
            return VisionAnalysisResult.model_validate(payload)
        except VisionAnalysisError:
            raise
        except Exception as exc:
            logger.exception("Gemini vision JSON parse failed (%s): %s", model_id, text)
            raise VisionAnalysisError() from exc
