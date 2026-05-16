from __future__ import annotations

from uuid import UUID

from app.config import settings
from app.database import get_supabase


async def create_draft_loan(
    *,
    crop_type: str,
    declared_acreage: float,
    requested_amount: float,
    user_id: UUID | None = None,
) -> dict[str, str]:
    """Insert a draft loan row; uses DEMO_PROFILE_ID when user_id is omitted."""
    resolved_user_id = user_id
    if resolved_user_id is None:
        if not settings.DEMO_PROFILE_ID:
            raise ValueError("user_id is required when DEMO_PROFILE_ID is not configured.")
        resolved_user_id = UUID(settings.DEMO_PROFILE_ID)

    client = get_supabase()
    profile = await (
        client.table("profiles")
        .select("id")
        .eq("id", str(resolved_user_id))
        .limit(1)
        .execute()
    )
    if profile is None or not profile.data:
        raise ValueError(f"Profile {resolved_user_id} not found.")

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
