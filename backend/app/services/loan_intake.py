from __future__ import annotations

from uuid import UUID

from app.database import get_supabase
from app.services.profile_resolver import resolve_profile_id


async def create_draft_loan(
    *,
    crop_type: str,
    declared_acreage: float,
    requested_amount: float,
    user_id: UUID | None = None,
) -> dict[str, str]:
    """Insert a draft loan row for the authenticated user's profile."""
    resolved_user_id = await resolve_profile_id(user_id)

    client = get_supabase()
    insert = await (
        client.table("loans")
        .insert(
            {
                "user_id": str(resolved_user_id),
                "crop_type": crop_type.strip(),
                "declared_acreage": declared_acreage,
                "requested_amount": requested_amount,
                "status": "draft",
            }
        )
        .execute()
    )
    if insert is None or not insert.data:
        raise RuntimeError("Failed to create loan.")

    row = insert.data[0]
    return {"status": "created", "loan_id": str(row["id"])}
