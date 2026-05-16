from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import TypeVar
from uuid import UUID

import httpx
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from app.config import settings
from app.database import get_supabase
from app.services.evaluation import run_evaluation_pipeline
from app.services.loan_intake import create_draft_loan
from app.services.seylan_api_service import (
    SeylanApiError,
    check_loan_repayment_status,
    generate_repayment_qr,
    get_payout_account_balance,
    get_source_account_balance,
    repay_loan_via_cefts,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/loans", tags=["loans"])

BLOCKED_STATUSES = frozenset({"approved", "disbursed", "underwriting"})
ALLOWED_IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
MAX_EVIDENCE_BYTES = 10 * 1024 * 1024
SUPABASE_RETRY_ATTEMPTS = 3

T = TypeVar("T")


async def _supabase_call(
    operation: Callable[[], Awaitable[T]],
    *,
    action: str,
) -> T:
    """Retry transient network failures talking to Supabase from Docker."""
    last_error: Exception | None = None
    for attempt in range(1, SUPABASE_RETRY_ATTEMPTS + 1):
        try:
            return await operation()
        except httpx.ConnectError as exc:
            last_error = exc
            logger.warning(
                "Supabase connect failed during %s (attempt %s/%s)",
                action,
                attempt,
                SUPABASE_RETRY_ATTEMPTS,
            )
            if attempt < SUPABASE_RETRY_ATTEMPTS:
                await asyncio.sleep(0.5 * attempt)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(
            f"Cannot reach Supabase while {action}. "
            "Check SUPABASE_URL in backend/.env, that the project is not paused, "
            "and that Docker has outbound internet access."
        ),
    ) from last_error


class CreateLoanRequest(BaseModel):
    crop_type: str = Field(..., min_length=1, examples=["Paddy"])
    declared_acreage: float = Field(..., gt=0, examples=[2.5])
    requested_amount: float = Field(..., ge=5000, examples=[75000.0])
    user_id: UUID | None = Field(
        default=None,
        description="Authenticated user's profile id (required).",
    )


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


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create a draft loan application",
)
async def create_loan(
    body: CreateLoanRequest,
    request: Request,
) -> dict[str, str]:
    _require_supabase(request)

    try:
        created = await create_draft_loan(
            crop_type=body.crop_type,
            declared_acreage=body.declared_acreage,
            requested_amount=body.requested_amount,
            user_id=body.user_id,
        )
    except ValueError as exc:
        msg = str(exc)
        status_code = (
            status.HTTP_401_UNAUTHORIZED
            if "logged in" in msg.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=msg) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create loan.",
        ) from exc

    logger.info("Created draft loan %s", created["loan_id"])
    return created


_LOAN_LIST_COLUMNS = (
    "id, user_id, crop_type, declared_acreage, requested_amount, "
    "ai_verified_acreage, crop_health_matrix, market_volatility_index, "
    "calculated_risk_score, rejection_reason, status, multimodal_evidence_url, "
    "transaction_reference, repayment_method, repayment_reference, "
    "repayment_qr_request_ref, repaid_at, created_at, "
    "profiles(district, payout_account_number, payout_bank_code)"
)


@router.get(
    "",
    summary="List loan applications for a farmer (service role; same user_id as create)",
)
async def list_loans(
    user_id: UUID,
    request: Request,
) -> list[dict[str, object]]:
    _require_supabase(request)
    client = get_supabase()
    response = await _supabase_call(
        lambda: client.table("loans")
        .select(_LOAN_LIST_COLUMNS)
        .eq("user_id", str(user_id))
        .order("created_at", desc=True)
        .execute(),
        action="list user loans",
    )
    return list(response.data or [])


@router.get(
    "/{loan_id}",
    summary="Get loan application status",
)
async def get_loan(loan_id: UUID, request: Request) -> dict[str, object]:
    _require_supabase(request)
    row = await _get_loan_row(
        loan_id,
        "id, status, crop_type, declared_acreage, requested_amount, "
        "calculated_risk_score, rejection_reason, transaction_reference, "
        "multimodal_evidence_url, ai_verified_acreage, crop_health_matrix, "
        "repayment_method, repayment_reference, repayment_qr_request_ref, repaid_at",
    )
    return row


async def _update_loan_row(loan_id: UUID, payload: dict[str, object]) -> None:
    client = get_supabase()
    await client.table("loans").update(payload).eq("id", str(loan_id)).execute()


async def _profile_payout_for_loan(loan_id: UUID) -> tuple[str, str]:
    row = await _get_loan_row(
        loan_id,
        "user_id, profiles(payout_account_number, payout_bank_code)",
    )
    profile = row.get("profiles")
    if isinstance(profile, list):
        profile = profile[0] if profile else {}
    if not isinstance(profile, dict):
        profile = {}
    account = (
        str(profile.get("payout_account_number") or "").strip()
        or settings.SEYLAN_CEFTS_DESTINATION_ACCOUNT
    )
    bank = (
        str(profile.get("payout_bank_code") or "").strip()
        or settings.SEYLAN_CEFTS_DESTINATION_BANK_CODE
    )
    return account, bank


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


def _extension_for_upload(file: UploadFile) -> str:
    if file.filename and "." in file.filename:
        ext = file.filename.rsplit(".", 1)[-1].lower()
        if ext in {"jpg", "jpeg", "png", "webp"}:
            return "jpg" if ext == "jpeg" else ext
    content_type = file.content_type or ""
    if "png" in content_type:
        return "png"
    if "webp" in content_type:
        return "webp"
    return "jpg"


@router.post(
    "/{loan_id}/evidence/upload",
    summary="Upload crop evidence image (server-side storage)",
)
async def upload_evidence(
    loan_id: UUID,
    request: Request,
    file: UploadFile = File(...),
) -> dict[str, str]:
    _require_supabase(request)
    await _get_loan_row(loan_id, "id")

    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must be JPEG, PNG, or WebP.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file.",
        )
    if len(data) > MAX_EVIDENCE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must be 10 MB or smaller.",
        )

    ext = _extension_for_upload(file)
    object_path = f"{loan_id}/{uuid.uuid4()}.{ext}"
    bucket = settings.SUPABASE_STORAGE_BUCKET

    client = get_supabase()

    async def _upload_to_storage() -> None:
        await client.storage.from_(bucket).upload(
            object_path,
            data,
            file_options={"content-type": content_type},
        )

    async def _attach_path_to_loan() -> None:
        await (
            client.table("loans")
            .update({"multimodal_evidence_url": object_path})
            .eq("id", str(loan_id))
            .execute()
        )

    await _supabase_call(_upload_to_storage, action="uploading crop evidence")
    await _supabase_call(_attach_path_to_loan, action="saving evidence path on loan")

    return {
        "status": "ok",
        "loan_id": str(loan_id),
        "multimodal_evidence_url": object_path,
    }


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


class SourceBalanceResponse(BaseModel):
    account_number: str
    available_balance: str | None
    ledger_balance: str | None
    currency: str | None
    transaction_reference: str
    banking_mode: str


class RepaymentQrResponse(BaseModel):
    transaction_reference: str
    request_ref_no: str
    qr_code: str
    response_code: str
    response_description: str
    banking_mode: str


class RepaymentCeftsResponse(BaseModel):
    transaction_reference: str
    banking_mode: str
    source_account: str
    source_bank_code: str
    destination_account: str
    destination_bank_code: str
    amount: float
    status: str


class RepaymentStatusResponse(BaseModel):
    paid: bool
    detection_method: str | None
    matched_reference: str | None
    banking_mode: str
    message: str
    loan_status: str


@router.get(
    "/banking/payout-balance",
    summary="Farmer payout account balance (CEFTS destination, live Inquiry when configured)",
)
async def payout_account_balance() -> SourceBalanceResponse:
    try:
        result = await get_payout_account_balance()
    except SeylanApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return SourceBalanceResponse(
        account_number=result.account_number,
        available_balance=result.available_balance,
        ledger_balance=result.ledger_balance,
        currency=result.currency,
        transaction_reference=result.transaction_reference,
        banking_mode=result.banking_mode,
    )


@router.get(
    "/banking/source-balance",
    summary="Treasury source account balance (live Inquiry API when configured)",
)
async def source_account_balance() -> SourceBalanceResponse:
    try:
        result = await get_source_account_balance()
    except SeylanApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return SourceBalanceResponse(
        account_number=result.account_number,
        available_balance=result.available_balance,
        ledger_balance=result.ledger_balance,
        currency=result.currency,
        transaction_reference=result.transaction_reference,
        banking_mode=result.banking_mode,
    )


@router.post(
    "/{loan_id}/repayment/qr",
    summary="Generate LankaQR for loan repayment (sandbox)",
)
def _require_repayable_status(loan_status: object) -> None:
    if loan_status not in ("approved", "disbursed", "repayment_pending"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Loan is not repayable (current: {loan_status}).",
        )


async def create_repayment_qr(loan_id: UUID, request: Request) -> RepaymentQrResponse:
    _require_supabase(request)

    row = await _get_loan_row(loan_id, "id, status, requested_amount")
    loan_status = row.get("status")
    if loan_status == "repaid":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Loan is already repaid.",
        )
    _require_repayable_status(loan_status)

    amount = float(row["requested_amount"])
    try:
        result = await generate_repayment_qr(amount, bill_no=str(loan_id))
    except SeylanApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    await _update_loan_row(
        loan_id,
        {
            "status": "repayment_pending",
            "repayment_method": "qr",
            "repayment_qr_request_ref": result.request_ref_no,
        },
    )

    return RepaymentQrResponse(
        transaction_reference=result.transaction_reference,
        request_ref_no=result.request_ref_no,
        qr_code=result.qr_code,
        response_code=result.response_code,
        response_description=result.response_description,
        banking_mode=result.banking_mode,
    )


@router.post(
    "/{loan_id}/repayment/cefts",
    summary="Repay loan via CEFTS (farmer account → treasury)",
)
async def create_repayment_cefts(loan_id: UUID, request: Request) -> RepaymentCeftsResponse:
    _require_supabase(request)

    row = await _get_loan_row(loan_id, "id, status, requested_amount")
    loan_status = row.get("status")
    if loan_status == "repaid":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Loan is already repaid.",
        )
    _require_repayable_status(loan_status)

    amount = float(row["requested_amount"])
    source_account, source_bank = await _profile_payout_for_loan(loan_id)

    try:
        reference, banking_mode = await repay_loan_via_cefts(
            amount,
            loan_id=str(loan_id),
            source_account=source_account,
            source_bank_code=source_bank,
        )
    except SeylanApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    await _update_loan_row(
        loan_id,
        {
            "status": "repaid",
            "repayment_method": "cefts",
            "repayment_reference": reference,
            "repaid_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    return RepaymentCeftsResponse(
        transaction_reference=reference,
        banking_mode=banking_mode,
        source_account=source_account,
        source_bank_code=source_bank,
        destination_account=settings.SEYLAN_SOURCE_ACCOUNT_NUMBER,
        destination_bank_code=settings.SEYLAN_SOURCE_BANK_CODE,
        amount=amount,
        status="repaid",
    )


@router.get(
    "/{loan_id}/repayment/status",
    summary="Poll QR (TransactionView) or treasury history for repayment",
)
async def get_repayment_status(loan_id: UUID, request: Request) -> RepaymentStatusResponse:
    _require_supabase(request)

    row = await _get_loan_row(
        loan_id,
        "id, status, requested_amount, repayment_qr_request_ref, repayment_reference",
    )
    loan_status = str(row.get("status", ""))
    amount = float(row["requested_amount"])

    try:
        result = await check_loan_repayment_status(
            loan_id=str(loan_id),
            amount=amount,
            loan_status=loan_status,
            repayment_qr_request_ref=row.get("repayment_qr_request_ref"),  # type: ignore[arg-type]
            repayment_reference=row.get("repayment_reference"),  # type: ignore[arg-type]
        )
    except SeylanApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    if result.paid and loan_status != "repaid":
        await _update_loan_row(
            loan_id,
            {
                "status": "repaid",
                "repayment_reference": result.matched_reference
                or row.get("repayment_reference"),
                "repaid_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        loan_status = "repaid"

    return RepaymentStatusResponse(
        paid=result.paid,
        detection_method=result.detection_method,
        matched_reference=result.matched_reference,
        banking_mode=result.banking_mode,
        message=result.message,
        loan_status=loan_status,
    )
