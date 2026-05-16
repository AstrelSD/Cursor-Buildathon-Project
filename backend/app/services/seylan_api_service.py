from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Literal, Optional

import httpx
from pydantic import BaseModel, Field

from app.config import settings

logger = logging.getLogger(__name__)

_HEX_TABLE = "0123456789ABCDEF"

INTERNAL_TRANSFER_PATH = "/Posting/Account/InternalTransfer/1.0/TransferFunds"
CEFTS_PATH = "/Posting/Account/Cefts/1.0/InitiateCEFTSTransfer"
GENERATE_QR_PATH = "/MerchantQR/1.0/GenerateQR"
TRANSACTION_VIEW_PATH = "/MerchantQR/1.0/TransactionView"
BALANCE_INQUIRY_PATH = "/Inquiry/Account/AccountInquiry/1.0/GetAccountBalance"
TRANSACTION_HISTORY_PATH = "/Inquiry/Account/AccountInquiry/1.0/GetAccountTransactions"
TRANSACTION_HISTORY_PATH_ALT = (
    "/Inquiry/Account/AccountInquiry/1.0/GetAccountTransactionHistory"
)

BankingMode = Literal["mock", "live"]

# 1x1 transparent PNG — placeholder until MerchantQR returns a real QR image.
MOCK_QR_DATA_URI = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAD0lEQVQ42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

QR_CHECKSUM_FIELDS = (
    "Request_ref_no",
    "Mid",
    "Tid",
    "Merchant_login_id",
    "Type",
    "Transaction_amount",
    "Bill_no",
    "Mobile_no",
)


class SeylanApiError(Exception):
    """Raised when the Seylan gateway returns a non-success status code."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[str] = None,
        transaction_reference: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.transaction_reference = transaction_reference


class InternalTransferResult(BaseModel):
    transaction_reference: str
    raw_response: dict[str, Any] = Field(default_factory=dict)


class CeftsTransferResult(BaseModel):
    transaction_reference: str
    transaction_id: Optional[str] = None
    approval_number: Optional[str] = None
    response_code: Optional[str] = None
    response_code_desc: Optional[str] = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


class GenerateQrResult(BaseModel):
    transaction_reference: str
    request_ref_no: str
    qr_code: str
    response_code: str
    response_description: str
    check_value: Optional[str] = None
    banking_mode: BankingMode = "live"
    raw_response: dict[str, Any] = Field(default_factory=dict)


class RepaymentStatusResult(BaseModel):
    paid: bool
    detection_method: Optional[str] = None
    matched_reference: Optional[str] = None
    banking_mode: BankingMode = "mock"
    message: str = ""


class AccountBalanceResult(BaseModel):
    transaction_reference: str
    account_number: str
    available_balance: Optional[str] = None
    ledger_balance: Optional[str] = None
    currency: Optional[str] = None
    banking_mode: BankingMode = "live"
    raw_response: dict[str, Any] = Field(default_factory=dict)


def mock_transaction_reference(*, label: str = "MOCK") -> str:
    """Seylan-style reference placeholder until live Posting returns a real ref."""
    stamp = datetime.now(timezone.utc).strftime("%y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:10].upper()
    return f"E{stamp}${label}{suffix}"


def mock_disbursement_result(
    *,
    loan_id: Optional[str] = None,
    amount: float | Decimal | str,
) -> tuple[str, BankingMode]:
    label = f"LOAN{str(loan_id or 'SIM')[:8].upper().replace('-', '')}"
    reference = mock_transaction_reference(label=label)
    logger.info(
        "Mock CEFTS disbursement LKR %s -> %s@%s ref=%s (SEYLAN_MOCK_BANKING)",
        amount,
        settings.SEYLAN_CEFTS_DESTINATION_ACCOUNT,
        settings.SEYLAN_CEFTS_DESTINATION_BANK_CODE,
        reference,
    )
    return reference, "mock"


def mock_account_balance_result(
    *,
    account_number: str,
    available_balance: str = "125000.00",
    ledger_balance: Optional[str] = None,
    label: str = "BAL",
) -> AccountBalanceResult:
    ledger = ledger_balance if ledger_balance is not None else available_balance
    return AccountBalanceResult(
        transaction_reference=mock_transaction_reference(label=label),
        account_number=account_number,
        available_balance=available_balance,
        ledger_balance=ledger,
        currency=settings.SEYLAN_CURRENCY_CODE,
        banking_mode="mock",
        raw_response={
            "simulated": True,
            "note": "SEYLAN_MOCK_BANKING or inquiry fallback",
        },
    )


def mock_generate_qr_result(
    *,
    amount: float | Decimal | str,
    bill_no: str = "",
) -> GenerateQrResult:
    ref_no = str(int(uuid.uuid4().int % 10**12)).zfill(12)[:12]
    return GenerateQrResult(
        transaction_reference=mock_transaction_reference(label="QR"),
        request_ref_no=ref_no,
        qr_code=MOCK_QR_DATA_URI,
        response_code="EN00",
        response_description="Mock success — enable live MerchantQR when sandbox is ready",
        banking_mode="mock",
        raw_response={
            "GenerateQR_Response": {
                "Status": {"Code": "0000"},
                "QR_Information": {
                    "Request_ref_no": ref_no,
                    "Response_code": "EN00",
                    "Response_description": "Mock QR placeholder",
                    "simulated": True,
                    "Transaction_amount": _format_amount(amount),
                    "Bill_no": bill_no,
                },
            }
        },
    )


def generate_hmac_sha512_checksum(secret_key: str, data_string: str) -> str:
    """
    Annexure 1: HMAC-SHA512 over the pipe-delimited data string, hex-encoded,
    then Base64-encoded before attaching to the API payload.
    """
    mac = hmac.new(
        secret_key.encode("utf-8"),
        data_string.encode("utf-8"),
        hashlib.sha512,
    ).digest()
    hex_digest = "".join(
        _HEX_TABLE[(byte >> 4) & 0xF] + _HEX_TABLE[byte & 0xF] for byte in mac
    )
    return base64.b64encode(hex_digest.encode("utf-8")).decode("utf-8")


def build_transaction_view_checksum_data(
    *,
    merchant_login_id: str,
    from_date: str,
    to_date: str,
    mid: str,
    tid: str = "",
    rrn: str = "",
) -> str:
    """Pipe-delimited checksum for MerchantQR TransactionView (manual section 7.2)."""
    return "|".join([merchant_login_id, from_date, to_date, mid, tid, rrn])


def build_generate_qr_checksum_data(
    *,
    request_ref_no: str,
    mid: str,
    tid: str = "",
    merchant_login_id: str,
    qr_type: str,
    transaction_amount: str = "",
    bill_no: str = "",
    mobile_no: str = "",
) -> str:
    """Pipe-delimited string for Generate QR request checksum (section 7.1 / Annexure 1)."""
    return "|".join(
        [
            request_ref_no,
            mid,
            tid,
            merchant_login_id,
            qr_type,
            transaction_amount,
            bill_no,
            mobile_no,
        ]
    )


def _format_amount(amount: float | Decimal | str) -> str:
    value = Decimal(str(amount))
    normalized = value.quantize(Decimal("0.01"))
    if normalized == normalized.to_integral():
        return str(int(normalized))
    return format(normalized, "f")


def _status_code(payload: dict[str, Any]) -> Optional[str]:
    status = payload.get("Status")
    if isinstance(status, dict):
        code = status.get("Code")
        return str(code) if code is not None else None
    return None


def _transaction_reference(payload: dict[str, Any]) -> Optional[str]:
    status = payload.get("Status")
    if isinstance(status, dict):
        ref = status.get("Transaction_Reference")
        return str(ref) if ref else None
    return None


def _response_root(raw: dict[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        nested = raw.get(key)
        if isinstance(nested, dict):
            return nested
    return raw


def _first_account_field(account: dict[str, Any], *keys: str) -> Optional[str]:
    for key in keys:
        value = account.get(key)
        if value is not None and str(value).strip() not in ("", "NaN"):
            return str(value)
    return None


def _parse_inquiry_balances(account: dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Map Seylan GetAccountBalance shapes to available/ledger/currency.

    Live sandbox (May 2026) returns balances on Account root, e.g.
    Current_available_balance / Ledger_balance / Currency_mnemonic.
    Some payloads nest them under Account.Balance instead.
    """
    nested = account.get("Balance")
    balance_block = nested if isinstance(nested, dict) else account

    available = _first_account_field(
        balance_block,
        "Current_available_balance",
        "Available_balance",
        "Available_Balance",
        "Current_cleared_balance",
    )
    ledger = _first_account_field(
        balance_block,
        "Ledger_balance",
        "Ledger_Balance",
        "Status_balance",
    )
    currency = _first_account_field(
        balance_block,
        "Currency_mnemonic",
        "Currency",
        "Currency_code",
    ) or _first_account_field(account, "Currency_mnemonic", "Currency_code")
    return available, ledger, currency


def _require_success(
    response_root: dict[str, Any],
    *,
    failure_label: str,
) -> str:
    code = _status_code(response_root)
    transaction_reference = _transaction_reference(response_root)
    if code == "0000" and transaction_reference:
        return transaction_reference
    status = response_root.get("Status", {})
    message = (
        status.get("Message")
        or status.get("Description")
        or failure_label
    )
    raise SeylanApiError(
        str(message),
        status_code=code,
        transaction_reference=transaction_reference,
    )


class _SeylanHttpClient:
    """Hackathon sandbox client — proxies Seylan with x-api-key auth only."""

    def __init__(self, timeout: float = 60.0) -> None:
        if not settings.seylan_configured:
            raise SeylanApiError(
                "Seylan sandbox is not configured. Set SEYLAN_API_KEY and SEYLAN_SANDBOX_BASE_URL."
            )
        self._api_key = settings.SEYLAN_API_KEY.get_secret_value()  # type: ignore[union-attr]
        self._base_url = settings.seylan_sandbox_base_url
        self._timeout = timeout

    async def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": self._api_key,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=body, headers=headers)

        try:
            payload = response.json()
        except ValueError as exc:
            raise SeylanApiError(
                f"Seylan sandbox returned non-JSON (HTTP {response.status_code})."
            ) from exc

        if response.status_code >= 400:
            raise SeylanApiError(
                f"Seylan sandbox HTTP {response.status_code}: {payload}",
                transaction_reference=_transaction_reference(payload),
            )

        return payload

    async def get(self, path: str, *, params: Optional[dict[str, str]] = None) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        headers = {
            "Accept": "application/json",
            "x-api-key": self._api_key,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(url, params=params or {}, headers=headers)

        try:
            payload = response.json()
        except ValueError as exc:
            raise SeylanApiError(
                f"Seylan sandbox returned non-JSON (HTTP {response.status_code})."
            ) from exc

        if response.status_code >= 400:
            raise SeylanApiError(
                f"Seylan sandbox HTTP {response.status_code}: {payload}",
            )

        return payload


class DisbursementService:
    """Fund transfers via hackathon sandbox (internal + CEFTS APIs from Web API manual)."""

    def __init__(self) -> None:
        self._client = _SeylanHttpClient()

    def build_internal_transfer_payload(
        self,
        *,
        amount: float | Decimal | str,
        destination_account: Optional[str] = None,
        source_account: Optional[str] = None,
        user_reference: Optional[str] = None,
    ) -> dict[str, Any]:
        """Construct FundsTransfer_Request JSON from section 1.1."""
        return {
            "FundsTransfer_Request": {
                "Account_category": settings.SEYLAN_ACCOUNT_CATEGORY,
                "Source_account_number": source_account or settings.SEYLAN_SOURCE_ACCOUNT_NUMBER,
                "Destination_account_number": destination_account
                or settings.SEYLAN_INTERNAL_DESTINATION_ACCOUNT,
                "Transaction_amount": _format_amount(amount),
                "Debit_transaction_code": "020",
                "Credit_transaction_code": "520",
                "User_reference": user_reference or f"AGRI-INT-{uuid.uuid4().hex[:8].upper()}",
                "Source_account_narration_1": "",
                "Source_account_narration_2": "",
                "Source_account_narration_3": "",
                "Destination_account_narration_1": "Agri-Lend disbursement",
                "Destination_account_narration_2": "",
                "Destination_account_narration_3": "",
                "Application_type": "",
                "Input_branch": "MLV ",
                "Input_user": "",
                "Workstation_id": "",
                "Posting_batch": "",
                "Charges_origination_account": "SRC",
                "Charge_code": "",
                "Charge_amount": "0",
            }
        }

    async def initiate_internal_transfer(
        self,
        amount: float | Decimal | str,
        *,
        destination_account: Optional[str] = None,
        source_account: Optional[str] = None,
        user_reference: Optional[str] = None,
    ) -> InternalTransferResult:
        body = self.build_internal_transfer_payload(
            amount=amount,
            destination_account=destination_account,
            source_account=source_account,
            user_reference=user_reference,
        )
        raw = await self._client.post(INTERNAL_TRANSFER_PATH, body)
        response_root = _response_root(raw, "FundsTransfer_Response")
        transaction_reference = _require_success(
            response_root,
            failure_label="Internal transfer failed",
        )
        return InternalTransferResult(
            transaction_reference=transaction_reference,
            raw_response=raw,
        )

    def build_cefts_payload(
        self,
        *,
        destination_account: str,
        destination_bank_code: str,
        amount: float | Decimal | str,
        reference: Optional[str] = None,
        destination_customer_name: Optional[str] = None,
        source_account_number: Optional[str] = None,
        source_customer_name: Optional[str] = None,
        source_bank_code: Optional[str] = None,
        processing_code: str = "482000",
        transaction_code: str = "52",
    ) -> dict[str, Any]:
        """Construct the exact CEFTS JSON body from section 2.1 of the Web API manual."""
        user_reference = reference or f"AGRI-{uuid.uuid4().hex[:12].upper()}"
        return {
            "CEFTSTransactionRequest": {
                "Processing_code": processing_code,
                "Transaction_code": transaction_code,
                "Transaction_amount": _format_amount(amount),
                "Card_acceptor_terminal_id": "",
                "Card_acceptor_id": "",
                "Terminal_location": "",
                "Channel_type": "ANY",
                "Account_category": settings.SEYLAN_ACCOUNT_CATEGORY,
                "Source_account_number": source_account_number
                or settings.SEYLAN_SOURCE_ACCOUNT_NUMBER,
                "Source_card_number": "",
                "Source_customer_name": source_customer_name
                or settings.SEYLAN_SOURCE_CUSTOMER_NAME,
                "Source_bank_code": source_bank_code or settings.SEYLAN_SOURCE_BANK_CODE,
                "Source_branch_code": "",
                "Source_wallet_number": "",
                "Destination_card_number": "",
                "Destination_account_number": destination_account,
                "Destination_bank_code": destination_bank_code,
                "Destination_customer_name": destination_customer_name
                or settings.SEYLAN_DEFAULT_DESTINATION_NAME,
                "Destination_branch_code": "",
                "Destination_wallet_number": "",
                "Currency_code": settings.SEYLAN_CURRENCY_CODE,
                "Reference": user_reference,
                "Particular_details": "",
                "Additional_data": "",
                "Authorized_user": "",
                "Customer_account_narration_1": "",
                "Customer_account_narration_2": "",
                "Customer_account_narration_3": "",
                "Internal_account_narration_1": "",
                "Internal_account_narration_2": "",
                "Internal_account_narration_3": "",
                "Application_type": [],
                "Input_branch": [],
                "Input_user": [],
                "Workstation_id": [],
                "Posting_batch": [],
                "Charges_origination_account": [],
                "Charge_code": [],
                "Charge_amount": [],
                "Charges_credit_branch": [],
                "Charges_narrative_1": [],
                "Charges_narrative_2": [],
                "Charges_narrative_3": [],
                "Existing_hold_amount": [],
                "Hold_reference": [],
            }
        }

    async def initiate_cefts_transfer(
        self,
        destination_account: str,
        bank_code: str,
        amount: float | Decimal | str,
        *,
        reference: Optional[str] = None,
        destination_customer_name: Optional[str] = None,
        source_account_number: Optional[str] = None,
        source_customer_name: Optional[str] = None,
        source_bank_code: Optional[str] = None,
    ) -> CeftsTransferResult:
        """
        POST InitiateCEFTSTransfer and return the gateway Transaction Reference.
        """
        body = self.build_cefts_payload(
            destination_account=destination_account,
            destination_bank_code=bank_code,
            amount=amount,
            reference=reference,
            destination_customer_name=destination_customer_name,
            source_account_number=source_account_number,
            source_customer_name=source_customer_name,
            source_bank_code=source_bank_code,
        )
        logger.info(
            "Initiating CEFTS transfer to %s@%s amount=%s ref=%s",
            destination_account,
            bank_code,
            body["CEFTSTransactionRequest"]["Transaction_amount"],
            body["CEFTSTransactionRequest"]["Reference"],
        )

        raw = await self._client.post(CEFTS_PATH, body)
        response_root = _response_root(raw, "CEFTSTransactionResponse")
        transaction_reference = _require_success(
            response_root,
            failure_label="CEFTS transfer failed",
        )

        detail = response_root.get("CEFTSTransaction_Detail", {})
        return CeftsTransferResult(
            transaction_reference=transaction_reference,
            transaction_id=detail.get("Transaction_id"),
            approval_number=detail.get("Approval_number"),
            response_code=detail.get("Response_code"),
            response_code_desc=detail.get("Response_code_desc"),
            raw_response=raw,
        )


async def disburse_loan_amount(
    amount: float | Decimal | str,
    *,
    loan_id: Optional[str] = None,
    destination_account: Optional[str] = None,
    bank_code: Optional[str] = None,
    use_internal_transfer: bool = False,
) -> tuple[str, BankingMode]:
    """
    Disburse an approved loan via CEFTS (or internal transfer).
    Returns (transaction_reference, banking_mode).
    """
    if settings.SEYLAN_MOCK_BANKING or not settings.seylan_disbursement_configured:
        return mock_disbursement_result(loan_id=loan_id, amount=amount)

    reference = f"LOAN-{loan_id}" if loan_id else None
    service = DisbursementService()

    try:
        if use_internal_transfer:
            result = await service.initiate_internal_transfer(
                amount,
                user_reference=reference,
                destination_account=destination_account,
            )
            return result.transaction_reference, "live"

        result = await service.initiate_cefts_transfer(
            destination_account=destination_account or settings.SEYLAN_CEFTS_DESTINATION_ACCOUNT,
            bank_code=bank_code or settings.SEYLAN_CEFTS_DESTINATION_BANK_CODE,
            amount=amount,
            reference=reference,
        )
        return result.transaction_reference, "live"
    except SeylanApiError as exc:
        if settings.SEYLAN_FALLBACK_TO_MOCK_ON_ERROR:
            logger.warning(
                "Live disbursement failed (%s); using mock reference for loan %s",
                exc,
                loan_id,
            )
            return mock_disbursement_result(loan_id=loan_id, amount=amount)
        raise


class AccountInquiryService:
    """Account balance inquiry (sandbox Inquiry product — currently live)."""

    def __init__(self) -> None:
        self._client = _SeylanHttpClient()

    async def get_account_balance(
        self,
        account_number: Optional[str] = None,
        *,
        account_category: Optional[str] = None,
    ) -> AccountBalanceResult:
        acct = account_number or settings.SEYLAN_SOURCE_ACCOUNT_NUMBER
        category = account_category or settings.SEYLAN_ACCOUNT_CATEGORY
        payload = await self._client.get(
            BALANCE_INQUIRY_PATH,
            params={"AccountCategory": category, "AccountNumber": acct},
        )
        root = payload.get("Account_Balance_Inquiry", payload)
        transaction_reference = _require_success(
            root,
            failure_label="Balance inquiry failed",
        )
        account = root.get("Account", {})
        if not isinstance(account, dict):
            account = {}
        available, ledger, currency = _parse_inquiry_balances(account)
        return AccountBalanceResult(
            transaction_reference=transaction_reference,
            account_number=acct,
            available_balance=available,
            ledger_balance=ledger,
            currency=currency or settings.SEYLAN_CURRENCY_CODE,
            banking_mode="live",
            raw_response=payload,
        )


async def _get_account_balance_with_fallback(
    account_number: str,
    *,
    mock_available_balance: str = "125000.00",
) -> AccountBalanceResult:
    # Inquiry works on the sandbox even when Posting/QR are mocked (SEYLAN_MOCK_BANKING).
    if not settings.seylan_configured:
        return mock_account_balance_result(
            account_number=account_number,
            available_balance=mock_available_balance,
        )

    try:
        return await AccountInquiryService().get_account_balance(account_number)
    except SeylanApiError as exc:
        if settings.SEYLAN_FALLBACK_TO_MOCK_ON_ERROR:
            logger.warning(
                "Live balance inquiry failed for %s (%s); returning mock balance",
                account_number,
                exc,
            )
            return mock_account_balance_result(
                account_number=account_number,
                available_balance=mock_available_balance,
            )
        raise


async def get_source_account_balance() -> AccountBalanceResult:
    return await _get_account_balance_with_fallback(
        settings.SEYLAN_SOURCE_ACCOUNT_NUMBER,
        mock_available_balance="500000.00",
    )


async def get_payout_account_balance() -> AccountBalanceResult:
    """
    Farmer-facing balance on the apply/dashboard flow.

    The CEFTS destination (12345678) may not support Inquiry; when live lookup
    fails we try the treasury source account so the UI can still show sandbox funds.
    """
    payout_account = settings.SEYLAN_CEFTS_DESTINATION_ACCOUNT
    if not settings.seylan_configured:
        return mock_account_balance_result(
            account_number=payout_account,
            available_balance="125000.00",
        )

    service = AccountInquiryService()
    candidates = [payout_account]
    if settings.SEYLAN_SOURCE_ACCOUNT_NUMBER not in candidates:
        candidates.append(settings.SEYLAN_SOURCE_ACCOUNT_NUMBER)

    last_error: Optional[Exception] = None
    for index, account_number in enumerate(candidates):
        try:
            result = await service.get_account_balance(account_number)
            if index > 0:
                logger.info(
                    "Payout balance inquiry used treasury source %s (CEFTS dest unavailable)",
                    account_number,
                )
            return result
        except SeylanApiError as exc:
            last_error = exc
            logger.warning("Balance inquiry failed for %s: %s", account_number, exc)

    if settings.SEYLAN_FALLBACK_TO_MOCK_ON_ERROR:
        logger.warning(
            "All payout balance inquiries failed; returning mock for %s",
            payout_account,
        )
        return mock_account_balance_result(
            account_number=payout_account,
            available_balance="125000.00",
        )
    if last_error is not None:
        raise last_error
    raise SeylanApiError("Balance inquiry failed")


async def generate_repayment_qr(
    amount: float | Decimal | str,
    *,
    bill_no: str = "",
) -> GenerateQrResult:
    if settings.SEYLAN_MOCK_BANKING or not settings.seylan_qr_configured:
        return mock_generate_qr_result(amount=amount, bill_no=bill_no)

    try:
        result = await RepaymentService().generate_lanka_qr(amount, bill_no=bill_no)
        result.banking_mode = "live"
        return result
    except SeylanApiError as exc:
        if settings.SEYLAN_FALLBACK_TO_MOCK_ON_ERROR:
            logger.warning("Live QR generation failed (%s); returning mock QR", exc)
            return mock_generate_qr_result(amount=amount, bill_no=bill_no)
        raise


class RepaymentService:
    """LankaQR merchant repayment collection (API 7.1 Generate QR)."""

    def __init__(self) -> None:
        if not settings.seylan_qr_configured:
            raise SeylanApiError(
                "QR repayment is not configured. Set merchant login, channel pass, and checksum key."
            )
        self._client = _SeylanHttpClient()

    def build_generate_qr_payload(
        self,
        *,
        amount: float | Decimal | str,
        request_ref_no: Optional[str] = None,
        qr_type: str = "1",
        tid: str = "",
        bill_no: str = "",
        mobile_no: str = "",
        transaction_currency: Optional[str] = None,
        device_id: str = "",
        store_label: str = "",
        loyalty_number: str = "",
        reference_label: str = "",
        customer_label: str = "",
        terminal_label: str = "",
        purpose_of_transaction: str = "",
        additional_customer_data_request: str = "",
        session_id: str = "",
        ip_address: str = "",
    ) -> dict[str, Any]:
        """Construct the exact Generate QR JSON body from section 7.1 of the Web API manual."""
        ref_no = request_ref_no or str(int(uuid.uuid4().int % 10**12)).zfill(12)[:12]
        formatted_amount = _format_amount(amount)
        mid = settings.seylan_merchant_mid
        merchant_login_id = settings.seylan_merchant_login_id
        merchant_login_pass = settings.seylan_merchant_login_pass

        checksum_data = build_generate_qr_checksum_data(
            request_ref_no=ref_no,
            mid=mid,
            tid=tid,
            merchant_login_id=merchant_login_id,
            qr_type=qr_type,
            transaction_amount=formatted_amount,
            bill_no=bill_no,
            mobile_no=mobile_no,
        )
        checksum_key = settings.SEYLAN_QR_CHECKSUM_KEY.get_secret_value()  # type: ignore[union-attr]
        check_sum = generate_hmac_sha512_checksum(checksum_key, checksum_data)

        return {
            "GenerateQR_Request": {
                "Institution_id": settings.SEYLAN_QR_INSTITUTION_ID,
                "Channel_user_id": settings.SEYLAN_QR_CHANNEL_USER_ID,
                "Channel_pass": settings.SEYLAN_QR_CHANNEL_PASS.get_secret_value(),  # type: ignore[union-attr]
                "Request_ref_no": ref_no,
                "Merchant_login_id": merchant_login_id,
                "Merchant_login_pass": merchant_login_pass,
                "Function": "generateQRAPI",
                "Device_id": device_id,
                "Type": qr_type,
                "Mid": mid,
                "Tid": tid,
                "Transaction_amount": formatted_amount,
                "Transaction_currency": transaction_currency
                or settings.SEYLAN_QR_TRANSACTION_CURRENCY,
                "Bill_no": bill_no,
                "Mobile_no": mobile_no,
                "Store_label": store_label,
                "Loyalty_number": loyalty_number,
                "Reference_label": reference_label,
                "Customer_label": customer_label,
                "Terminal_label": terminal_label,
                "Purpose_of_transaction": purpose_of_transaction,
                "Additional_customer_data_request": additional_customer_data_request,
                "Session_id": session_id,
                "Ip_address": ip_address,
                "Check_sum": check_sum,
            }
        }

    async def generate_lanka_qr(
        self,
        amount: float | Decimal | str,
        *,
        request_ref_no: Optional[str] = None,
        qr_type: str = "1",
        tid: str = "",
        bill_no: str = "",
        mobile_no: str = "",
    ) -> GenerateQrResult:
        """
        POST GenerateQR and return QR payload plus Transaction Reference.
        """
        body = self.build_generate_qr_payload(
            amount=amount,
            request_ref_no=request_ref_no,
            qr_type=qr_type,
            tid=tid,
            bill_no=bill_no,
            mobile_no=mobile_no,
        )
        request_block = body["GenerateQR_Request"]
        logger.info(
            "Generating LankaQR mid=%s ref=%s amount=%s",
            request_block["Mid"],
            request_block["Request_ref_no"],
            request_block["Transaction_amount"],
        )

        raw = await self._client.post(GENERATE_QR_PATH, body)
        response_root = _response_root(raw, "GenerateQR_Response")
        transaction_reference = _require_success(
            response_root,
            failure_label="QR generation failed",
        )

        qr_info = response_root.get("QR_Information", {})
        return GenerateQrResult(
            transaction_reference=transaction_reference,
            request_ref_no=str(qr_info.get("Request_ref_no") or request_block["Request_ref_no"]),
            qr_code=str(qr_info.get("QR_code", "")),
            response_code=str(qr_info.get("Response_code", "")),
            response_description=str(qr_info.get("Response_description", "")),
            check_value=qr_info.get("Check_value"),
            banking_mode="live",
            raw_response=raw,
        )

    async def inquiry_merchant_transactions(
        self,
        *,
        from_date: str,
        to_date: str,
        rrn: str = "",
    ) -> list[dict[str, Any]]:
        """POST TransactionView (manual 7.2) — list merchant QR settlements."""
        ref_no = str(int(uuid.uuid4().int % 10**12)).zfill(12)[:12]
        mid = settings.seylan_merchant_mid
        merchant_login_id = settings.seylan_merchant_login_id
        merchant_login_pass = settings.seylan_merchant_login_pass
        checksum_key = settings.SEYLAN_QR_CHECKSUM_KEY.get_secret_value()  # type: ignore[union-attr]
        checksum_data = build_transaction_view_checksum_data(
            merchant_login_id=merchant_login_id,
            from_date=from_date,
            to_date=to_date,
            mid=mid,
            tid="",
            rrn=rrn,
        )
        check_sum = generate_hmac_sha512_checksum(checksum_key, checksum_data)
        body = {
            "TransactionView_Request": {
                "Institution_id": settings.SEYLAN_QR_INSTITUTION_ID,
                "Channel_user_id": settings.SEYLAN_QR_CHANNEL_USER_ID,
                "Channel_pass": settings.SEYLAN_QR_CHANNEL_PASS.get_secret_value(),  # type: ignore[union-attr]
                "Request_ref_no": ref_no,
                "Merchant_login_id": merchant_login_id,
                "Merchant_login_pass": merchant_login_pass,
                "Function": "viewMerTxnAPI",
                "From_date": from_date,
                "To_date": to_date,
                "Rrn": rrn,
                "Mid": mid,
                "Tid": "",
                "Customer_card_no": "",
                "Additional_value_first": "",
                "Additional_value_second": "",
                "Records_per_page_count": "50",
                "Page_no": "1",
                "Ip_address": "",
                "Check_sum": check_sum,
            }
        }
        raw = await self._client.post(TRANSACTION_VIEW_PATH, body)
        response_root = _response_root(raw, "TransactionView_Response")
        _require_success(response_root, failure_label="QR transaction inquiry failed")
        info = response_root.get("TransactionView_Information", {})
        details = info.get("transactionDetails", [])
        if isinstance(details, list):
            return [d for d in details if isinstance(d, dict)]
        return []


def _history_date_range(*, days: int = 14) -> tuple[str, str]:
    today = datetime.now(timezone.utc).date()
    start = today.fromordinal(today.toordinal() - days)
    return start.isoformat(), today.isoformat()


def _extract_history_transactions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    root = payload.get("TransactionHistoryInquiryResponse", payload)
    transactions = root.get("Transaction", [])
    if isinstance(transactions, list):
        return [t for t in transactions if isinstance(t, dict)]
    return []


def _transaction_matches_repayment(
    txn: dict[str, Any],
    *,
    loan_id: str,
    amount: float | Decimal | str,
    search_tokens: tuple[str, ...],
) -> bool:
    formatted_amount = _format_amount(amount)
    amount_candidates = {formatted_amount, f"{formatted_amount}.00", f"-{formatted_amount}"}
    posting = str(txn.get("Posting_amount", "")).replace(",", "").strip()
    if posting.lstrip("-") not in {a.lstrip("-") for a in amount_candidates}:
        if not any(
            posting.lstrip("-").startswith(a.lstrip("-"))
            for a in amount_candidates
            if a
        ):
            return False

    haystack = " ".join(
        str(txn.get(key, "") or "")
        for key in (
            "Users_own_reference",
            "Narrative_1",
            "Narrative_2",
            "Narrative_3",
            "Narrative_4",
            "Additional_line_1",
            "Additional_line_2",
            "Additional_line_3",
            "Additional_line_4",
        )
    ).upper()
    loan_token = loan_id.replace("-", "").upper()
    for token in search_tokens:
        if token.upper() in haystack or loan_token in haystack.replace("-", ""):
            return True
    return False


async def get_treasury_transaction_history(
    *,
    days: int = 14,
) -> list[dict[str, Any]]:
    """Treasury account credits/debits (manual GetAccountTransactions)."""
    if not settings.seylan_configured:
        return []

    from_date, to_date = _history_date_range(days=days)
    client = _SeylanHttpClient()
    account = settings.SEYLAN_SOURCE_ACCOUNT_NUMBER
    category = settings.SEYLAN_ACCOUNT_CATEGORY
    param_sets = (
        {
            "AccountCategory": category,
            "AccountNumber": account,
            "StartDate": from_date,
            "EndDate": to_date,
        },
        {
            "AccountCategory": category,
            "AccountNumber": account,
            "FromDate": from_date,
            "ToDate": to_date,
        },
    )
    paths = (TRANSACTION_HISTORY_PATH, TRANSACTION_HISTORY_PATH_ALT)
    last_error: Optional[Exception] = None
    for path in paths:
        for params in param_sets:
            try:
                payload = await client.get(path, params=params)
                txns = _extract_history_transactions(payload)
                if txns:
                    return txns
                code = _status_code(
                    payload.get("TransactionHistoryInquiryResponse", payload)
                )
                if code == "0000":
                    return []
            except Exception as exc:  # noqa: BLE001 — try alternate path/params
                last_error = exc
                logger.debug("Transaction history %s failed: %s", path, exc)
    if last_error:
        logger.warning("Treasury transaction history unavailable: %s", last_error)
    return []


async def repay_loan_via_cefts(
    amount: float | Decimal | str,
    *,
    loan_id: str,
    source_account: str,
    source_bank_code: str,
    source_customer_name: Optional[str] = None,
) -> tuple[str, BankingMode]:
    """Farmer → treasury CEFTS repayment (reverse of disbursement)."""
    reference = f"REPAY-{loan_id}"
    if settings.SEYLAN_MOCK_BANKING or not settings.seylan_disbursement_configured:
        ref = mock_transaction_reference(label="REPAY")
        logger.info(
            "Mock CEFTS repayment LKR %s from %s@%s ref=%s",
            amount,
            source_account,
            source_bank_code,
            ref,
        )
        return ref, "mock"

    service = DisbursementService()
    try:
        result = await service.initiate_cefts_transfer(
            destination_account=settings.SEYLAN_SOURCE_ACCOUNT_NUMBER,
            bank_code=settings.SEYLAN_SOURCE_BANK_CODE,
            amount=amount,
            reference=reference,
            destination_customer_name=settings.SEYLAN_SOURCE_CUSTOMER_NAME,
            source_account_number=source_account,
            source_customer_name=source_customer_name or settings.SEYLAN_DEFAULT_DESTINATION_NAME,
            source_bank_code=source_bank_code,
        )
        return result.transaction_reference, "live"
    except SeylanApiError as exc:
        if settings.SEYLAN_FALLBACK_TO_MOCK_ON_ERROR:
            logger.warning("Live CEFTS repayment failed (%s); using mock", exc)
            return mock_transaction_reference(label="REPAY"), "mock"
        raise


async def check_loan_repayment_status(
    *,
    loan_id: str,
    amount: float | Decimal | str,
    loan_status: str,
    repayment_qr_request_ref: Optional[str] = None,
    repayment_reference: Optional[str] = None,
) -> RepaymentStatusResult:
    """Detect repayment via Merchant TransactionView (7.2) and treasury history (2C)."""
    if loan_status == "repaid":
        return RepaymentStatusResult(
            paid=True,
            detection_method="already_repaid",
            matched_reference=repayment_reference,
            banking_mode="live",
            message="Loan is already marked repaid.",
        )

    if loan_status not in ("disbursed", "repayment_pending", "approved"):
        return RepaymentStatusResult(
            paid=False,
            message=f"Loan status '{loan_status}' is not awaiting repayment.",
        )

    search_tokens = (f"REPAY-{loan_id}", loan_id, repayment_qr_request_ref or "")
    formatted_amount = _format_amount(amount)

    if settings.seylan_qr_configured and not settings.SEYLAN_MOCK_BANKING:
        from_date, to_date = _history_date_range(days=30)
        try:
            details = await RepaymentService().inquiry_merchant_transactions(
                from_date=from_date,
                to_date=to_date,
            )
            for detail in details:
                txn_amount = str(detail.get("Transaction_amount", "")).strip()
                if txn_amount not in (formatted_amount, f"{formatted_amount}.00"):
                    continue
                rrn = str(detail.get("Retrieval_refernce_no", "") or "")
                if repayment_qr_request_ref and repayment_qr_request_ref not in rrn:
                    bill_match = loan_id[:8] in str(detail).upper()
                    if not bill_match:
                        continue
                return RepaymentStatusResult(
                    paid=True,
                    detection_method="qr_transaction_view",
                    matched_reference=rrn or str(detail.get("Stan", "")),
                    banking_mode="live",
                    message="QR payment found in merchant transaction view.",
                )
        except SeylanApiError as exc:
            logger.warning("Merchant TransactionView inquiry failed: %s", exc)

    if settings.seylan_configured:
        try:
            for txn in await get_treasury_transaction_history(days=21):
                if _transaction_matches_repayment(
                    txn,
                    loan_id=loan_id,
                    amount=amount,
                    search_tokens=search_tokens,
                ):
                    ref = str(txn.get("Users_own_reference", "") or "") or str(
                        txn.get("Narrative_4", "") or ""
                    )
                    return RepaymentStatusResult(
                        paid=True,
                        detection_method="treasury_transaction_history",
                        matched_reference=ref or None,
                        banking_mode="live",
                        message="Repayment credit found on treasury account.",
                    )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Treasury history scan failed: %s", exc)

    return RepaymentStatusResult(
        paid=False,
        banking_mode="mock" if settings.SEYLAN_MOCK_BANKING else "live",
        message="No matching repayment found yet. Pay via QR or CEFTS, then refresh.",
    )
