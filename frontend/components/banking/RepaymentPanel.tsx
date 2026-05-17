"use client";

import { QRCodeSVG } from "qrcode.react";
import {
  Building2,
  CheckCircle2,
  Loader2,
  QrCode,
  RefreshCw,
  Send,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import {
  FARMER_PAYOUT_ACCOUNT,
  FARMER_PAYOUT_BANK_CODE,
  FARMER_PAYOUT_BANK_NAME,
} from "@/constants/banking";
import {
  fetchPayoutAccountBalance,
  fetchRepaymentQr,
  fetchRepaymentStatus,
  initiateRepaymentCefts,
  type AccountBalanceResponse,
  type RepaymentQrResponse,
} from "@/lib/api";
import { formatBalanceDisplay, formatLkr } from "@/lib/format";
import type { LoanRow } from "@/lib/supabase";

type Tab = "qr" | "cefts";

type RepaymentPanelProps = {
  loan: LoanRow;
  onRepaid?: () => void;
};

function qrPayload(qr: RepaymentQrResponse): string {
  const code = qr.qr_code.trim();
  if (code.startsWith("data:image")) return code;
  return code;
}

function isImageDataUri(value: string): boolean {
  return value.startsWith("data:image");
}

export function RepaymentPanel({ loan, onRepaid }: RepaymentPanelProps) {
  const [tab, setTab] = useState<Tab>("qr");
  const [qr, setQr] = useState<RepaymentQrResponse | null>(null);
  const [balance, setBalance] = useState<AccountBalanceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const isRepaid = loan.status === "repaid";
  const canRepay =
    loan.status === "disbursed" || loan.status === "repayment_pending";

  const loadBalance = useCallback(async () => {
    try {
      const result = await fetchPayoutAccountBalance();
      setBalance(result);
    } catch {
      /* balance uses hackathon test account for all farmers */
    }
  }, []);

  useEffect(() => {
    if (!canRepay && !isRepaid) return;
    void loadBalance();
  }, [canRepay, isRepaid, loadBalance]);

  const pollStatus = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const status = await fetchRepaymentStatus(loan.id);
      setStatusMessage(status.message);
      if (status.paid) onRepaid?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Status check failed.");
    } finally {
      setBusy(false);
    }
  }, [loan.id, onRepaid]);

  useEffect(() => {
    if (!canRepay || tab !== "qr" || !qr) return;
    const interval = setInterval(() => {
      void pollStatus();
    }, 8000);
    return () => clearInterval(interval);
  }, [canRepay, tab, qr, pollStatus]);

  async function handleGenerateQr() {
    setBusy(true);
    setError(null);
    try {
      const result = await fetchRepaymentQr(loan.id);
      setQr(result);
      setStatusMessage("Scan the QR with your banking app, then we will detect payment.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate QR.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCeftsRepay() {
    setBusy(true);
    setError(null);
    try {
      const result = await initiateRepaymentCefts(loan.id);
      setStatusMessage(
        `CEFTS sent to treasury. Reference ${result.transaction_reference}.`,
      );
      onRepaid?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "CEFTS repayment failed.");
    } finally {
      setBusy(false);
    }
  }

  if (isRepaid) {
    return (
      <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
        <div className="flex items-center gap-2 text-emerald-900">
          <CheckCircle2 className="h-5 w-5" aria-hidden />
          <p className="font-semibold">Loan repaid in full</p>
        </div>
        {loan.repayment_reference ? (
          <p className="mt-2 font-mono text-xs text-emerald-800">
            Ref: {loan.repayment_reference}
          </p>
        ) : null}
        {loan.repayment_method ? (
          <p className="mt-1 text-sm text-emerald-800">
            Method: {loan.repayment_method.toUpperCase()}
          </p>
        ) : null}
      </div>
    );
  }

  if (!canRepay) return null;

  const qrValue = qr ? qrPayload(qr) : "";

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-5">
      <h3 className="text-base font-semibold text-gray-900 sm:text-lg">
        Repay {formatLkr(loan.requested_amount)}
      </h3>
      <p className="mt-1 text-sm text-gray-600">
        Pay the full loan amount back to Agri-Lend via LankaQR or CEFTS.
      </p>

      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={() => setTab("qr")}
          className={`flex min-h-11 flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium ${
            tab === "qr"
              ? "bg-[#2E7D32] text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          <QrCode className="h-4 w-4" aria-hidden />
          LankaQR
        </button>
        <button
          type="button"
          onClick={() => setTab("cefts")}
          className={`flex min-h-11 flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium ${
            tab === "cefts"
              ? "bg-[#2E7D32] text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          <Send className="h-4 w-4" aria-hidden />
          CEFTS
        </button>
      </div>

      {balance ? (
        <div className="mt-4 rounded-lg border border-gray-100 bg-gray-50 px-3 py-2 text-sm">
          <p className="text-xs text-gray-500">
            Sandbox balance (test account {FARMER_PAYOUT_ACCOUNT})
          </p>
          <p className="font-semibold text-gray-900">
            {formatBalanceDisplay(balance.available_balance, balance.currency)}
          </p>
        </div>
      ) : null}

      {error ? (
        <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </p>
      ) : null}

      {statusMessage ? (
        <p className="mt-3 text-sm text-gray-600">{statusMessage}</p>
      ) : null}

      {tab === "qr" ? (
        <div className="mt-4 space-y-4">
          {!qr ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => void handleGenerateQr()}
              className="w-full rounded-lg bg-[#2E7D32] py-2.5 text-sm font-medium text-white hover:bg-[#1b5e20] disabled:opacity-50"
            >
              {busy ? (
                <span className="inline-flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating QR…
                </span>
              ) : (
                "Generate repayment QR"
              )}
            </button>
          ) : (
            <>
              <div className="flex flex-col items-center rounded-lg border border-dashed border-gray-200 bg-white p-4">
                {isImageDataUri(qrValue) ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={qrValue}
                    alt="Repayment QR code"
                    className="h-48 w-48 object-contain"
                  />
                ) : qrValue ? (
                  <QRCodeSVG value={qrValue} size={192} level="M" />
                ) : (
                  <p className="text-sm text-gray-500">No QR payload returned.</p>
                )}
                <p className="mt-3 text-center text-xs text-gray-500">
                  Bill no: {loan.id.slice(0, 8)}… · Ref {qr.request_ref_no}
                </p>
              </div>
              <button
                type="button"
                disabled={busy}
                onClick={() => void pollStatus()}
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-[#2E7D32] py-2.5 text-sm font-medium text-[#2E7D32] hover:bg-green-50 disabled:opacity-50"
              >
                {busy ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                Check payment status
              </button>
              <p className="text-xs text-gray-500">
                We poll Seylan Merchant TransactionView (§7.2) and treasury transaction
                history for your payment.
              </p>
            </>
          )}
        </div>
      ) : (
        <div className="mt-4 space-y-3 text-sm">
          <dl className="space-y-2 rounded-lg bg-gray-50 p-3">
            <div>
              <dt className="text-gray-500">From (your account on file)</dt>
              <dd className="font-mono text-gray-900">
                Profile account · balance shown from sandbox test ID{" "}
                {FARMER_PAYOUT_ACCOUNT}
              </dd>
            </div>
            <div>
              <dt className="text-gray-500">To (Agri-Lend treasury)</dt>
              <dd className="font-mono text-xs text-gray-900">
                Uses Seylan sandbox treasury via CEFTS
              </dd>
            </div>
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Building2 className="h-3 w-3" aria-hidden />
              {FARMER_PAYOUT_BANK_NAME} ({FARMER_PAYOUT_BANK_CODE})
            </div>
          </dl>
          <button
            type="button"
            disabled={busy}
            onClick={() => void handleCeftsRepay()}
            className="w-full rounded-lg bg-[#2E7D32] py-2.5 text-sm font-medium text-white hover:bg-[#1b5e20] disabled:opacity-50"
          >
            {busy ? (
              <span className="inline-flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Processing CEFTS…
              </span>
            ) : (
              `Pay ${formatLkr(loan.requested_amount)} via CEFTS`
            )}
          </button>
        </div>
      )}
    </div>
  );
}
