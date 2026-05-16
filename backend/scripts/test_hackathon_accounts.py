"""Verify hackathon test accounts in config and against sandbox."""

import asyncio
import json
import sys

import httpx

API_KEY = "aa16d36b-fea1-45a2-ace7-81042174244f"
BASE = "http://34.21.206.87:3000"
HEADERS = {"x-api-key": API_KEY, "Accept": "application/json", "Content-Type": "application/json"}

# Hackathon brief accounts
SOURCE = "064000012548001"
INT_DEST = "001213437904100"
CEFTS_DEST = "12345678"
CEFTS_BANK = "6990"


async def main() -> None:
    print("=== Configured in app (config.py / .env) ===")
    print(f"  Source:              {SOURCE}")
    print(f"  Internal destination: {INT_DEST}")
    print(f"  CEFTS default:       {CEFTS_DEST} @ bank {CEFTS_BANK}")
    print(f"  CEFTS alt (not default): 1546266 @ bank 6000")
    print()

    async with httpx.AsyncClient(timeout=45.0) as client:

        async def balance(account: str) -> None:
            r = await client.get(
                f"{BASE}/Inquiry/Account/AccountInquiry/1.0/GetAccountBalance",
                params={"AccountCategory": "EXT", "AccountNumber": account},
                headers=HEADERS,
            )
            code = None
            if r.status_code == 200:
                code = (
                    r.json()
                    .get("Account_Balance_Inquiry", {})
                    .get("Status", {})
                    .get("Code")
                )
            print(f"  Balance {account}: HTTP {r.status_code} Code={code}")

        print("=== Live sandbox checks ===")
        await balance(SOURCE)
        await balance(INT_DEST)

        int_body = {
            "FundsTransfer_Request": {
                "Account_category": "EXT",
                "Source_account_number": SOURCE,
                "Destination_account_number": INT_DEST,
                "Transaction_amount": "10.00",
                "User_reference": "HACKATHON-INT-TEST",
                "Input_branch": "MLV ",
                "Charges_origination_account": "SRC",
                "Charge_amount": "0",
            }
        }
        r = await client.post(
            f"{BASE}/Posting/Account/InternalTransfer/1.0/TransferFunds",
            json=int_body,
            headers=HEADERS,
        )
        print(f"  Internal {SOURCE} -> {INT_DEST}: HTTP {r.status_code}")
        print(f"    {r.text[:120]}")

        for dest, bank in [("12345678", "6990"), ("1546266", "6000")]:
            body = {
                "CEFTSTransactionRequest": {
                    "Processing_code": "482000",
                    "Transaction_code": "52",
                    "Transaction_amount": "10",
                    "Channel_type": "ANY",
                    "Account_category": "EXT",
                    "Source_account_number": SOURCE,
                    "Source_customer_name": "Cursor Buildathon 5",
                    "Source_bank_code": "6287",
                    "Destination_account_number": dest,
                    "Destination_bank_code": bank,
                    "Destination_customer_name": "Agri-Lend Farmer",
                    "Currency_code": "LKR",
                    "Reference": f"HACKATHON-CEFTS-{bank}",
                }
            }
            r = await client.post(
                f"{BASE}/Posting/Account/Cefts/1.0/InitiateCEFTSTransfer",
                json=body,
                headers=HEADERS,
            )
            print(f"  CEFTS {SOURCE} -> {dest} @ {bank}: HTTP {r.status_code}")
            print(f"    {r.text[:120]}")


if __name__ == "__main__":
    asyncio.run(main())
