"""Probe hackathon Seylan sandbox — which API products respond."""

from __future__ import annotations

import asyncio
import json
import sys

import httpx

API_KEY = "aa16d36b-fea1-45a2-ace7-81042174244f"
BASE = "http://34.21.206.87:3000"
HEADERS = {
    "x-api-key": API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json",
}


def summarize(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:100]

    if isinstance(payload, dict):
        if "error" in payload:
            return str(payload["error"])[:100]
        if "ErrorCode" in payload:
            return f"{payload.get('ErrorCode')}: {payload.get('ErrorMessage', '')}"[:100]
        for value in payload.values():
            if isinstance(value, dict) and "Status" in value:
                status = value["Status"]
                code = status.get("Code")
                ref = status.get("Transaction_Reference", "")
                msg = status.get("Message") or status.get("Description") or ""
                return f"Status.Code={code} ref={ref} {msg}"[:120]
    return json.dumps(payload)[:100]


async def probe() -> list[tuple[str, str, str, int, str, bool]]:
    rows: list[tuple[str, str, str, int, str, bool]] = []

    async with httpx.AsyncClient(timeout=45.0) as client:

        async def get_probe(category: str, name: str, path: str, params: dict) -> None:
            r = await client.get(f"{BASE}{path}", params=params, headers=HEADERS)
            ok = r.status_code == 200 and "Status.Code=0000" in summarize(r)
            rows.append((category, name, "GET", r.status_code, summarize(r), ok))

        async def post_probe(category: str, name: str, path: str, body: dict) -> None:
            r = await client.post(f"{BASE}{path}", json=body, headers=HEADERS)
            ok = r.status_code == 200 and "Status.Code=0000" in summarize(r)
            rows.append((category, name, "POST", r.status_code, summarize(r), ok))

        # --- Inquiry (read-only) ---
        await get_probe(
            "Inquiry",
            "Account balance",
            "/Inquiry/Account/AccountInquiry/1.0/GetAccountBalance",
            {"AccountCategory": "EXT", "AccountNumber": "064000012548001"},
        )
        await get_probe(
            "Inquiry",
            "Account transaction history",
            "/Inquiry/Account/AccountInquiry/1.0/GetAccountTransactionHistory",
            {
                "AccountCategory": "EXT",
                "AccountNumber": "064000012548001",
                "FromDate": "2026-01-01",
                "ToDate": "2026-05-16",
            },
        )

        # --- Posting / disbursement ---
        await post_probe(
            "Posting",
            "Internal transfer",
            "/Posting/Account/InternalTransfer/1.0/TransferFunds",
            {
                "FundsTransfer_Request": {
                    "Account_category": "EXT",
                    "Source_account_number": "064000012548001",
                    "Destination_account_number": "001213437904100",
                    "Transaction_amount": "10.00",
                    "User_reference": "PROBE-INT-001",
                    "Input_branch": "MLV ",
                    "Charges_origination_account": "SRC",
                    "Charge_amount": "0",
                }
            },
        )
        await post_probe(
            "Posting",
            "CEFTS transfer",
            "/Posting/Account/Cefts/1.0/InitiateCEFTSTransfer",
            {
                "CEFTSTransactionRequest": {
                    "Processing_code": "482000",
                    "Transaction_code": "52",
                    "Transaction_amount": "10",
                    "Card_acceptor_terminal_id": "",
                    "Card_acceptor_id": "",
                    "Terminal_location": "",
                    "Channel_type": "ANY",
                    "Account_category": "EXT",
                    "Source_account_number": "064000012548001",
                    "Source_card_number": "",
                    "Source_customer_name": "Cursor Buildathon 5",
                    "Source_bank_code": "6287",
                    "Source_branch_code": "",
                    "Source_wallet_number": "",
                    "Destination_card_number": "",
                    "Destination_account_number": "12345678",
                    "Destination_bank_code": "6990",
                    "Destination_customer_name": "Agri-Lend Farmer",
                    "Destination_branch_code": "",
                    "Destination_wallet_number": "",
                    "Currency_code": "LKR",
                    "Reference": "PROBE-CEFTS-001",
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
            },
        )

        # --- QR Merchant (repayment) ---
        await post_probe(
            "QR Merchant",
            "Generate QR",
            "/MerchantQR/1.0/GenerateQR",
            {
                "GenerateQR_Request": {
                    "Institution_id": "1",
                    "Channel_user_id": "MerchantAPI",
                    "Channel_pass": "placeholder",
                    "Request_ref_no": "123456789012",
                    "Merchant_login_id": "TCURSOR5op",
                    "Merchant_login_pass": "TPassword@55#5",
                    "Function": "generateQRAPI",
                    "Type": "1",
                    "Mid": "TESTCURSOR5",
                    "Tid": "",
                    "Transaction_amount": "10",
                    "Transaction_currency": "144",
                    "Check_sum": "dGVzdA==",
                }
            },
        )

        # --- LankaQR acquirer ---
        await post_probe(
            "LankaQR",
            "Initiate LankaQR",
            "/QR/LankaQR/1.0/InitiateLankaQRTransaction",
            {"LankaQRTransaction_Request": {"Retrieval_reference": "PROBE-LQR-001"}},
        )

        # --- JustPay ---
        await post_probe(
            "JustPay",
            "Initiate JustPay",
            "/JustPay/Acquirer/1.0/InitiateJustPayTransaction",
            {"JustPayTransaction_Request": {"Retrieval_reference": "PROBE-JP-001"}},
        )

        # --- Doc sample (not expected) ---
        await get_probe(
            "Doc sample",
            "Sample service",
            "/Inquiries/1.0/SampleService",
            {"AccountCategory": "EXT", "AccountNumber": "064000012548001"},
        )

    return rows


def main() -> None:
    rows = asyncio.run(probe())
    working = [r for r in rows if r[5]]
    reachable = [r for r in rows if r[3] != 404]
    blocked = [r for r in rows if r[3] in (401, 403)]

    print("SEYLAN SANDBOX PROBE")
    print(f"Base: {BASE}\n")
    print(f"{'Category':<14} {'API':<28} {'Method':<6} {'HTTP':<5} {'OK':<4} Summary")
    print("-" * 100)
    for cat, name, method, status, summary, ok in rows:
        mark = "YES" if ok else "no"
        print(f"{cat:<14} {name:<28} {method:<6} {status:<5} {mark:<4} {summary}")

    print("\n=== WORKING (HTTP 200 + Code 0000) ===")
    for r in working:
        print(f"  - {r[1]} ({r[2]} {r[3]})")

    print("\n=== REACHABLE BUT NOT SUCCESS ===")
    for r in reachable:
        if not r[5]:
            print(f"  - {r[1]}: HTTP {r[3]} — {r[4]}")

    print("\n=== NOT CONFIGURED (404) ===")
    for r in rows:
        if r[3] == 404:
            print(f"  - {r[1]}")

    sys.exit(0 if working else 1)


if __name__ == "__main__":
    main()
