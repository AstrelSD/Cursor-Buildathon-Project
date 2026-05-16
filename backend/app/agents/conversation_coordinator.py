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
If a field is missing, infer reasonable defaults only when strongly implied; otherwise use sensible demo defaults: acreage 2.5, amount 75000."""


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
        return parsed

    async def _extract_gemini(self, transcript: str) -> LoanIntakeFields:
        assert self._gemini is not None
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            "Respond with JSON only: "
            '{"crop_type":"...","declared_acreage":0.0,"requested_amount":0.0}\n\n'
            f"Transcript:\n{transcript}"
        )
        response = await self._gemini.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        raw = (response.text or "").strip()
        data = json.loads(raw)
        return LoanIntakeFields.model_validate(data)

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

        acreage = 2.5
        acre_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:acre|acres|acreage)",
            lower,
        )
        if acre_match:
            acreage = float(acre_match.group(1))

        amount = 75_000.0
        amount_match = re.search(
            r"(?:lkr|rs\.?|rupees?|amount|loan)?\s*(\d[\d,]*(?:\.\d+)?)\s*(?:k|thousand)?",
            lower,
        )
        if amount_match:
            raw = amount_match.group(1).replace(",", "")
            val = float(raw)
            if "thousand" in lower or "k" in lower[max(0, amount_match.start() - 5) : amount_match.end() + 5]:
                val *= 1000
            amount = max(val, 5000)

        return LoanIntakeFields(
            crop_type=crop,
            declared_acreage=acreage,
            requested_amount=amount,
        )
