from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.database import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfilePayoutResponse(BaseModel):
    payout_account_number: str | None
    payout_bank_code: str | None


class UpdateProfilePayoutRequest(BaseModel):
    user_id: UUID
    payout_account_number: str = Field(..., min_length=6, max_length=20)
    payout_bank_code: str = Field(..., min_length=4, max_length=4)


def _require_supabase(request: Request) -> None:
    if getattr(request.app.state, "supabase", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client is not available. Check backend configuration.",
        )


def _map_profile_error(exc: Exception) -> HTTPException:
    message = str(exc)
    lowered = message.lower()
    if "payout_account_number" in lowered or "payout_bank_code" in lowered:
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Database migration missing payout columns. "
                "Apply supabase/migrations/20260516160000_repayment_and_payout_profile.sql "
                "in the Supabase SQL editor, then try again."
            ),
        )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Profile update failed: {message}",
    )


@router.get("/payout", summary="Get farmer payout account on file")
async def get_profile_payout(user_id: UUID, request: Request) -> ProfilePayoutResponse:
    _require_supabase(request)
    client = get_supabase()
    try:
        response = await (
            client.table("profiles")
            .select("payout_account_number, payout_bank_code")
            .eq("id", str(user_id))
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise _map_profile_error(exc) from exc

    rows = response.data or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for this user.",
        )
    row = rows[0]
    return ProfilePayoutResponse(
        payout_account_number=row.get("payout_account_number"),
        payout_bank_code=row.get("payout_bank_code"),
    )


@router.patch("/payout", summary="Save farmer payout account on profile")
async def update_profile_payout(
    body: UpdateProfilePayoutRequest,
    request: Request,
) -> ProfilePayoutResponse:
    _require_supabase(request)
    client = get_supabase()
    payload = {
        "payout_account_number": body.payout_account_number.strip(),
        "payout_bank_code": body.payout_bank_code.strip(),
    }
    try:
        response = await (
            client.table("profiles")
            .update(payload)
            .eq("id", str(body.user_id))
            .execute()
        )
    except Exception as exc:
        logger.exception("Profile payout update failed for user %s", body.user_id)
        raise _map_profile_error(exc) from exc

    rows = response.data or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found for this user.",
        )
    row = rows[0]
    return ProfilePayoutResponse(
        payout_account_number=row.get("payout_account_number"),
        payout_bank_code=row.get("payout_bank_code"),
    )
