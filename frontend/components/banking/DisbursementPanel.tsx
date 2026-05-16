"use client";

import { Building2, CheckCircle2, Loader2, Wallet } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import {
  FARMER_PAYOUT_ACCOUNT,
  FARMER_PAYOUT_BANK_CODE,
  FARMER_PAYOUT_BANK_NAME,
} from "@/constants/banking";
import { PATH_DASHBOARD } from "@/constants/routes";
import {
  fetchPayoutAccountBalance,
  type AccountBalanceResponse,
} from "@/lib/api";
import { formatBalanceDisplay, formatLkr } from "@/lib/format";

type DisbursementPanelProps = {
  loanAmount: number;
  transactionReference: string | null;
  status: "approved" | "disbursed";
  showDashboardLink?: boolean;
  className?: string;
};

export function DisbursementPanel({
  loanAmount,
  transactionReference,
  status,
  showDashboardLink = true,
  className = "",
}: DisbursementPanelProps) {
  const [balance, setBalance] = useState<AccountBalanceResponse | null>(null);
  const [balanceError, setBalanceError] = useState<string | null>(null);
  const [loadingBalance, setLoadingBalance] = useState(false);

  const isDisbursed = status === "disbursed";

  useEffect(() => {
    if (!isDisbursed) return;

    let cancelled = false;
    setLoadingBalance(true);
    setBalanceError(null);

    void fetchPayoutAccountBalance()
      .then((result) => {
        if (!cancelled) setBalance(result);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setBalanceError(
            err instanceof Error ? err.message : "Could not load account balance.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingBalance(false);
      });

    return () => {
      cancelled = true;
    };
  }, [isDisbursed, loanAmount, transactionReference]);

  return (
    <div
      className={`rounded-xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-5 shadow-sm ${className}`}
    >
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#2E7D32] text-white">
          {isDisbursed ? (
            <CheckCircle2 className="h-5 w-5" aria-hidden />
          ) : (
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
          )}
        </span>
        <div>
          <h3 className="font-semibold text-emerald-950">
            {isDisbursed ? "Funds sent via CEFTS" : "Loan approved"}
          </h3>
          <p className="mt-0.5 text-sm text-emerald-900/80">
            {isDisbursed
              ? "Your approved amount was transferred to your linked payout account."
              : "Disbursement is being finalized on the Seylan sandbox."}
          </p>
        </div>
      </div>

      <dl className="mt-4 space-y-3 text-sm">
        <DetailRow label="Transfer type" value="CEFTS (interbank)" />
        <DetailRow
          label="Credited to"
          value={`${FARMER_PAYOUT_ACCOUNT} · ${FARMER_PAYOUT_BANK_NAME} (${FARMER_PAYOUT_BANK_CODE})`}
        />
        <DetailRow label="Loan amount" value={formatLkr(loanAmount)} highlight />
        {transactionReference ? (
          <DetailRow label="Bank reference" value={transactionReference} mono />
        ) : null}
      </dl>

      {isDisbursed ? (
        <div className="mt-4 rounded-lg border border-emerald-100 bg-white/80 px-4 py-3">
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-gray-500">
            <Wallet className="h-3.5 w-3.5" aria-hidden />
            Payout account balance
            {balance?.banking_mode === "mock" ? (
              <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold normal-case text-amber-900">
                Demo
              </span>
            ) : null}
          </div>
          {loadingBalance ? (
            <p className="mt-2 flex items-center gap-2 text-sm text-gray-600">
              <Loader2 className="h-4 w-4 animate-spin" />
              Checking balance…
            </p>
          ) : balanceError ? (
            <p className="mt-2 text-sm text-amber-800">{balanceError}</p>
          ) : balance ? (
            <p className="mt-1 text-2xl font-semibold text-gray-900">
              {formatBalanceDisplay(balance.available_balance, balance.currency)}
            </p>
          ) : null}
          <p className="mt-1 flex items-center gap-1 text-xs text-gray-500">
            <Building2 className="h-3 w-3" aria-hidden />
            Account {FARMER_PAYOUT_ACCOUNT}
          </p>
        </div>
      ) : (
        <p className="mt-4 text-xs text-emerald-800/80">
          CEFTS transfer is processing. Refresh in a moment or open your dashboard.
        </p>
      )}

      {showDashboardLink ? (
        <Link
          href={PATH_DASHBOARD}
          className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-[#2E7D32] hover:underline"
        >
          View on dashboard
        </Link>
      ) : null}
    </div>
  );
}

function DetailRow({
  label,
  value,
  highlight,
  mono,
}: {
  label: string;
  value: string;
  highlight?: boolean;
  mono?: boolean;
}) {
  return (
    <div className="flex flex-col gap-0.5 sm:flex-row sm:justify-between sm:gap-4">
      <dt className="text-gray-500">{label}</dt>
      <dd
        className={`sm:text-right ${
          highlight ? "font-semibold text-[#2E7D32]" : "text-gray-900"
        } ${mono ? "break-all font-mono text-xs" : ""}`}
      >
        {value}
      </dd>
    </div>
  );
}
