from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.database import get_supabase
from app.services.evaluation import run_evaluation_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/loans", tags=["loans"])

BLOCKED_STATUSES = frozenset({"approved", "disbursed", "underwriting"})


class AttachEvidenceRequest(BaseModel):
    """Storage path or Supabase URL for crop evidence in loan-evidence bucket."""

    evidence_url: str = Field(
        ...,
        min_length=1,
        examples=["farm1.jpg", "loan-evidence/farm1.jpg"],
        description="Object path (e.g. farm1.jpg) or public/signed Supabase Storage URL.",
    )


def _require_supabase(request: Request) -> None:
    if getattr(request.app.state, "supabase", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase client is not available. Check backend configuration.",
        )


async def _get_loan_row(loan_id: UUID, columns: str) -> dict[str, object]:
    client = get_supabase()
    response = await (
        client.table("loans").select(columns).eq("id", str(loan_id)).limit(1).execute()
    )
    rows = response.data if response is not None else None
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Loan {loan_id} not found.",
        )
    return rows[0]


@router.patch(
    "/{loan_id}/evidence",
    summary="Attach uploaded crop evidence to a loan",
)
async def attach_evidence(
    loan_id: UUID,
    body: AttachEvidenceRequest,
    request: Request,
) -> dict[str, str]:
    _require_supabase(request)
    await _get_loan_row(loan_id, "id")

    client = get_supabase()
    await (
        client.table("loans")
        .update({"multimodal_evidence_url": body.evidence_url.strip()})
        .eq("id", str(loan_id))
        .execute()
    )

    return {
        "status": "ok",
        "loan_id": str(loan_id),
        "multimodal_evidence_url": body.evidence_url.strip(),
    }


@router.post(
    "/{loan_id}/evaluate",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger multi-agent underwriting pipeline",
)
async def evaluate_loan(
    loan_id: UUID,
    background_tasks: BackgroundTasks,
    request: Request,
) -> dict[str, str]:
    _require_supabase(request)
    row = await _get_loan_row(loan_id, "id, status, multimodal_evidence_url")
    current_status = row["status"]
    if current_status in BLOCKED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Loan {loan_id} is in status '{current_status}' and cannot be re-evaluated."
            ),
        )

    if current_status == "analyzing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Loan {loan_id} is already being analyzed.",
        )

    if not row.get("multimodal_evidence_url"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Loan has no multimodal_evidence_url. Upload crop evidence first.",
        )

    background_tasks.add_task(run_evaluation_pipeline, loan_id)
    logger.info("Queued evaluation pipeline for loan %s", loan_id)

    return {
        "status": "accepted",
        "loan_id": str(loan_id),
        "message": "Multi-agent underwriting pipeline started.",
    }
