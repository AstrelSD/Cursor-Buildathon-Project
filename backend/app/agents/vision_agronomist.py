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

logger = logging.getLogger(__name__)

VISION_SYSTEM_PROMPT = """You are VisionAgronomistAgent, an expert agronomic computer-vision underwriter
for smallholder farms in Sri Lanka. Analyze the crop field imagery and return ONLY valid JSON with
exactly these keys:
- estimated_acreage (positive number)
- chlorophyll_index (0.0 to 1.0)
- disease_detected (boolean)
- health_score (0 to 100)

Evaluate blight, pests, chlorosis, dead-leaf coverage, and field boundaries.
For normal readable crop field photos, health_score should reflect visible vigor (typically 50-95).
Only use health_score 0 when the image is not a readable agricultural field."""


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


def _mock_vision_result(declared_acreage: float) -> VisionAnalysisResult:
    """Deterministic fallback for demos when Gemini quota is unavailable."""
    return VisionAnalysisResult(
        estimated_acreage=round(declared_acreage * 0.98, 2),
        chlorophyll_index=0.82,
        disease_detected=False,
        health_score=88.0,
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
    ) -> VisionAnalysisResult:
        if not image_bytes:
            raise VisionAnalysisError()

        prompt = (
            f"The farmer declared {declared_acreage:.2f} acres. "
            "Estimate cultivated acreage from visible field boundaries. "
            'Return JSON only, e.g. {"estimated_acreage": 2.4, "chlorophyll_index": 0.82, '
            '"disease_detected": false, "health_score": 88}'
        )

        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            types.Part.from_text(text=prompt),
        ]
        config = types.GenerateContentConfig(
            system_instruction=VISION_SYSTEM_PROMPT,
            temperature=0.1,
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
                return self._parse_response(response.text, model_id)
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
            logger.warning("Using MOCK_VISION_ON_FAILURE fallback for declared_acreage=%s", declared_acreage)
            return _mock_vision_result(declared_acreage)

        if quota_hit:
            raise VisionQuotaError() from last_error

        raise VisionAnalysisError() from last_error

    @staticmethod
    def _parse_response(text: Optional[str], model_id: str) -> VisionAnalysisResult:
        if not text:
            raise VisionAnalysisError()

        try:
            payload = json.loads(_extract_json_payload(text))
            result = VisionAnalysisResult.model_validate(payload)
        except Exception as exc:
            logger.exception("Gemini vision JSON parse failed (%s): %s", model_id, text)
            raise VisionAnalysisError() from exc

        if result.health_score <= 0 or result.estimated_acreage <= 0:
            raise VisionAnalysisError()

        logger.info("Vision analysis succeeded via model=%s health_score=%s", model_id, result.health_score)
        return result
