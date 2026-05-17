from __future__ import annotations

import json
import logging
import re
from typing import Optional

from google import genai
from google.genai import types as genai_types
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.config import settings
from app.constants.crops import normalize_crop_type

logger = logging.getLogger(__name__)

GPT_MODEL = "gpt-4o"

SYSTEM_PROMPT = """You extract structured Sri Lankan smallholder farm loan intake from conversation transcripts.
Farmers may speak Tamil, Sinhala, English, or a mix — always output English crop names and numeric fields.
Return crop_type (e.g. Paddy, Maize, Corn, Tea, Coconut, Vegetables, Fruits), declared_acreage as a positive number in acres, and requested_amount in LKR (minimum 5000).
Normalize informal speech in any language ("two and a half acres", "75 thousand rupees", Tamil/Sinhala number words) into numeric values.
Map common Tamil crop terms when heard: நெல்/விதைப்பயிர் → Paddy, மக்காச்சோளம்/சோளம் → Maize or Corn, தேயிலை → Tea, பழம்/காய்கறி → Fruits or Vegetables.
Map common Sinhala crop terms when heard: වී/කුඹුරු → Paddy, ඉරිඟු/මයිස්/ඉරිඟු වගා → Maize or Corn, තේ → Tea, පොල් → Coconut, එළවළු → Vegetables, පළතුරු → Fruits.
Treat "corn" and "maize" as Corn unless the farmer clearly says maize/மக்காச்சோளம்.
Sinhala number phrases (e.g. අක්කර, රුපියල්, දහයිදාහයි) should become acres and LKR amounts.
If crop_type cannot be determined from the transcript, use "Paddy" only when rice/paddy/நெல்/වී is mentioned; otherwise pick the closest supported crop from context. Never ignore an explicit crop name in Tamil, Sinhala, or English.
If acreage or amount is missing, use defaults only when strongly implied: acreage 2.5, amount 75000."""


class LoanIntakeFields(BaseModel):
    crop_type: str = Field(..., min_length=1)
    declared_acreage: float = Field(..., gt=0)
    requested_amount: float = Field(..., ge=5000)


class ConversationCoordinator:
    """OpenAI GPT-4o (preferred) or Gemini fallback for voice transcript → loan intake."""

    def __init__(self) -> None:
        self._openai: Optional[AsyncOpenAI] = None
        if settings.openai_configured:
            self._openai = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY.get_secret_value()  # type: ignore[union-attr]
            )
        self._gemini: Optional[genai.Client] = None
        if settings.google_genai_configured:
            self._gemini = genai.Client(
                api_key=settings.GOOGLE_GENAI_API_KEY.get_secret_value()  # type: ignore[union-attr]
            )

    async def extract_intake(self, transcript: str) -> LoanIntakeFields:
        text = transcript.strip()
        if len(text) < 8:
            raise ValueError("Transcript too short to extract loan details.")

        if self._openai is not None:
            try:
                return await self._extract_openai(text)
            except Exception:
                logger.exception("OpenAI intake extraction failed; trying fallback")

        if self._gemini is not None:
            try:
                return await self._extract_gemini(text)
            except Exception:
                logger.exception("Gemini intake extraction failed; trying heuristic")

        return self._extract_heuristic(text)

    async def _extract_openai(self, transcript: str) -> LoanIntakeFields:
        assert self._openai is not None
        completion = await self._openai.beta.chat.completions.parse(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": transcript},
            ],
            response_format=LoanIntakeFields,
        )
        parsed = completion.choices[0].message.parsed
        if parsed is None:
            raise ValueError("OpenAI returned no structured intake.")
        return parsed.model_copy(
            update={"crop_type": normalize_crop_type(parsed.crop_type)},
        )

    async def _extract_gemini(self, transcript: str) -> LoanIntakeFields:
        assert self._gemini is not None
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            "Respond with JSON only: "
            '{"crop_type":"...","declared_acreage":0.0,"requested_amount":0.0}\n\n'
            f"Transcript:\n{transcript}"
        )
        response = await self._gemini.aio.models.generate_content(
            model=settings.GEMINI_INTAKE_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        raw = (response.text or "").strip()
        data = json.loads(raw)
        fields = LoanIntakeFields.model_validate(data)
        return fields.model_copy(
            update={"crop_type": normalize_crop_type(fields.crop_type)},
        )

    @staticmethod
    def _parse_acreage(lower: str) -> Optional[float]:
        acre_patterns = (
            r"(\d+(?:\.\d+)?)\s*(?:acres?|acreage|\bac\b)",
            r"(?:acre|acres|acreage)\s*(?:of\s*)?(\d+(?:\.\d+)?)",
        )
        for pattern in acre_patterns:
            match = re.search(pattern, lower)
            if match:
                return float(match.group(1))
        return None

    @staticmethod
    def _parse_amount(lower: str, acreage: Optional[float]) -> Optional[float]:
        amount_patterns = (
            r"(?:lkr|rs\.?|rupees?|rupee|loan|amount|need|want|borrow)\s*(?:of\s*)?(\d[\d,]*(?:\.\d+)?)\s*(?:k|thousand)?",
            r"(\d[\d,]*(?:\.\d+)?)\s*(?:k|thousand)\s*(?:lkr|rs\.?|rupees?)?",
            r"(\d[\d,]*(?:\.\d+)?)\s*(?:lkr|rs\.?|rupees?)",
        )
        for pattern in amount_patterns:
            match = re.search(pattern, lower)
            if not match:
                continue
            val = ConversationCoordinator._money_token(
                match.group(1),
                match.group(0),
            )
            if val is not None and val >= 5000:
                return val

        candidates: list[float] = []
        for match in re.finditer(r"(\d[\d,]*(?:\.\d+)?)\s*(k|thousand)?", lower):
            tail = lower[match.end() : match.end() + 12]
            if re.match(r"\s*(?:acre|acres|acreage|\bac\b)", tail):
                continue
            val = ConversationCoordinator._money_token(
                match.group(1),
                match.group(0),
            )
            if val is not None and val >= 5000:
                candidates.append(val)

        if not candidates:
            return None
        best = max(candidates)
        if acreage is not None and best == acreage:
            alt = [n for n in candidates if n != acreage]
            return max(alt) if alt else None
        return best

    @staticmethod
    def _money_token(raw: str, context: str) -> Optional[float]:
        try:
            val = float(raw.replace(",", ""))
        except ValueError:
            return None
        ctx = context.lower()
        if "k" in ctx or "thousand" in ctx:
            val *= 1000
        return val

    @staticmethod
    def _extract_heuristic(transcript: str) -> LoanIntakeFields:
        lower = transcript.lower()
        crop = "Paddy"
        crop_aliases = (
            ("paddy", "Paddy"),
            ("rice", "Paddy"),
            ("maize", "Maize"),
            ("corn", "Corn"),
            ("tea", "Tea"),
            ("coconut", "Coconut"),
            ("vegetable", "Vegetables"),
            ("vegetables", "Vegetables"),
            ("fruit", "Fruits"),
            ("fruits", "Fruits"),
        )
        for needle, label in crop_aliases:
            if needle in lower:
                crop = label
                break

        parsed_acreage = ConversationCoordinator._parse_acreage(lower)
        acreage = parsed_acreage if parsed_acreage is not None else 2.5

        parsed_amount = ConversationCoordinator._parse_amount(lower, parsed_acreage)
        amount = parsed_amount if parsed_amount is not None else 75_000.0

        return LoanIntakeFields(
            crop_type=normalize_crop_type(crop),
            declared_acreage=acreage,
            requested_amount=amount,
        )
