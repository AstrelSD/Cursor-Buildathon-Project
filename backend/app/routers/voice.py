from __future__ import annotations

import logging
from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.agents.conversation_coordinator import ConversationCoordinator
from app.config import settings
from app.services.loan_intake import create_draft_loan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


class VoiceIntakeRequest(BaseModel):
    transcript: str = Field(
        ...,
        min_length=8,
        description="Farmer speech transcript from ElevenLabs conversation.",
    )


class VoiceIntakeResponse(BaseModel):
    status: str
    loan_id: str
    crop_type: str
    declared_acreage: float
    requested_amount: float


def _require_voice_config() -> None:
    if not settings.elevenlabs_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ElevenLabs is not configured. Set ELEVENLABS_API_KEY in backend/.env",
        )


@router.get("/signed-url", summary="Get signed WebSocket URL for private ElevenLabs agent")
async def get_signed_url() -> dict[str, str]:
    _require_voice_config()
    if not settings.ELEVENLABS_AGENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ELEVENLABS_AGENT_ID is not configured.",
        )

    api_key = settings.ELEVENLABS_API_KEY.get_secret_value()  # type: ignore[union-attr]
    url = "https://api.elevenlabs.io/v1/convai/conversation/get-signed-url"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            url,
            params={"agent_id": settings.ELEVENLABS_AGENT_ID},
            headers={"xi-api-key": api_key},
        )

    if response.status_code != 200:
        logger.error("ElevenLabs signed-url error: %s", response.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to obtain ElevenLabs signed URL.",
        )

    body = response.json()
    signed_url = body.get("signed_url")
    if not signed_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ElevenLabs did not return a signed_url.",
        )
    return {"signed_url": signed_url}


@router.post(
    "/intake",
    status_code=status.HTTP_201_CREATED,
    summary="Extract loan fields from voice transcript and create draft loan",
)
async def voice_intake(body: VoiceIntakeRequest) -> VoiceIntakeResponse:
    coordinator = ConversationCoordinator()
    try:
        fields = await coordinator.extract_intake(body.transcript)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Voice intake extraction failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract loan details from transcript.",
        ) from exc

    try:
        created = await create_draft_loan(
            crop_type=fields.crop_type,
            declared_acreage=fields.declared_acreage,
            requested_amount=fields.requested_amount,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Draft loan creation failed after voice intake")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create draft loan.",
        ) from exc

    return VoiceIntakeResponse(
        status="created",
        loan_id=created["loan_id"],
        crop_type=fields.crop_type,
        declared_acreage=fields.declared_acreage,
        requested_amount=fields.requested_amount,
    )
