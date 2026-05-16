from __future__ import annotations

import re
from uuid import UUID

from app.database import get_supabase

_PHONE_RE = re.compile(r"^\+94[0-9]{9}$")


async def _profile_exists(user_id: UUID) -> bool:
    client = get_supabase()
    result = await (
        client.table("profiles")
        .select("id")
        .eq("id", str(user_id))
        .limit(1)
        .execute()
    )
    return bool(result and result.data)


async def resolve_profile_id(user_id: UUID | None) -> UUID:
    """Resolve the authenticated user's profile id for loan creation."""
    if user_id is None:
        raise ValueError(
            "You must be logged in to submit a loan application. "
            "Register or log in, then try again."
        )

    if await _profile_exists(user_id):
        return user_id

    raise ValueError(
        "Your farmer profile was not found. Log out and complete registration "
        "(district and phone required), then try again."
    )
