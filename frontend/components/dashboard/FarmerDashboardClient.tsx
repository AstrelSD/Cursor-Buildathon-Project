"use client";

import Link from "next/link";
import { Loader2, Sprout } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { DisbursementPanel } from "@/components/banking/DisbursementPanel";
import { RepaymentPanel } from "@/components/banking/RepaymentPanel";
import { PayoutAccountForm } from "@/components/dashboard/PayoutAccountForm";
import { useAuth } from "@/components/providers/AuthProvider";
import { PATH_APPLY, PATH_LOGIN } from "@/constants/routes";
import { formatLkr } from "@/lib/format";
import { fetchUserLoans, subscribeUserLoans } from "@/lib/loans";
import { loanDistrict, type LoanRow } from "@/lib/supabase";

function statusLabel(status: LoanRow["status"]): string {
  switch (status) {
    case "draft":
      return "Draft";
    case "analyzing":
      return "Analyzing";
    case "underwriting":
      return "Underwriting";
    case "approved":
      return "Approved";
    case "disbursed":
      return "Disbursed";
    case "repayment_pending":
      return "Awaiting payment";
    case "repaid":
      return "Repaid";
    case "rejected":
      return "Rejected";
    default:
      return status;
  }
}

function statusTone(status: LoanRow["status"]): string {
  if (status === "repaid") return "bg-blue-100 text-blue-900";
  if (status === "repayment_pending") return "bg-amber-100 text-amber-900";
  if (status === "disbursed" || status === "approved") {
    return "bg-emerald-100 text-emerald-900";
  }
  if (status === "rejected") return "bg-red-100 text-red-900";
  if (status === "underwriting" || status === "analyzing") {
    return "bg-amber-100 text-amber-900";
  }
  return "bg-gray-100 text-gray-700";
}

export function FarmerDashboardClient() {
  const { session, isLoading, isAuthenticated } = useAuth();
  const userId = session?.user?.id;
  const [loans, setLoans] = useState<LoanRow[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const refreshLoans = useCallback(async () => {
    if (!userId) return;
    try {
      setLoans(await fetchUserLoans(userId));
      setLoadError(null);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Could not load loans.");
    }
  }, [userId]);

  useEffect(() => {
    if (!userId) return;
    setLoadError(null);
    return subscribeUserLoans(userId, setLoans, setLoadError);
  }, [userId]);

  const latestDisbursed = useMemo(
    () =>
      loans.find((loan) =>
        ["disbursed", "repayment_pending", "repaid"].includes(loan.status),
      ),
    [loans],
  );

  const latestApproved = useMemo(
    () => loans.find((loan) => loan.status === "approved"),
    [loans],
  );

  const highlightLoan = latestDisbursed ?? latestApproved;

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center py-16 text-sm text-gray-500">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        Loading…
      </div>
    );
  }

  if (!isAuthenticated || !userId) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-4 py-16 text-center">
        <p className="text-lg font-semibold text-gray-900">Log in to view your loans</p>
        <Link
          href={PATH_LOGIN}
          className="mt-6 rounded-full bg-[#2E7D32] px-6 py-2.5 text-sm font-medium text-white hover:bg-[#1b5e20]"
        >
          Log in
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-4xl space-y-8">
      <header>
        <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">Your farm loans</h1>
        <p className="mt-2 text-sm text-gray-600">
          Track applications, repayments (LankaQR or CEFTS), and payout balance.
        </p>
      </header>

      <PayoutAccountForm userId={userId} />

      {highlightLoan &&
      (highlightLoan.status === "disbursed" ||
        highlightLoan.status === "approved" ||
        highlightLoan.status === "repayment_pending" ||
        highlightLoan.status === "repaid") ? (
        <DisbursementPanel
          loanAmount={highlightLoan.requested_amount}
          transactionReference={highlightLoan.transaction_reference}
          status={
            highlightLoan.status === "approved"
              ? "approved"
              : "disbursed"
          }
          showDashboardLink={false}
        />
      ) : null}

      {loadError ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {loadError}
        </div>
      ) : null}

      {loans.length === 0 && !loadError ? (
        <div className="rounded-2xl border border-dashed border-gray-200 bg-white px-6 py-12 text-center">
          <Sprout className="mx-auto h-10 w-10 text-[#2E7D32]/60" aria-hidden />
          <p className="mt-4 font-medium text-gray-900">No applications yet</p>
          <p className="mt-1 text-sm text-gray-600">
            Start a voice or form application to get funded via CEFTS.
          </p>
          <Link
            href={PATH_APPLY}
            className="mt-6 inline-flex rounded-full bg-[#2E7D32] px-6 py-2.5 text-sm font-medium text-white hover:bg-[#1b5e20]"
          >
            Apply for a loan
          </Link>
        </div>
      ) : (
        <ul className="space-y-4">
          {loans.map((loan) => (
            <li
              key={loan.id}
              className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-gray-900">{loan.crop_type}</p>
                  <p className="mt-0.5 text-sm text-gray-500">
                    {loanDistrict(loan)} · {loan.declared_acreage} acres
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${statusTone(loan.status)}`}
                >
                  {statusLabel(loan.status)}
                </span>
              </div>
              <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-gray-500">Requested</dt>
                  <dd className="font-medium text-gray-900">
                    {formatLkr(loan.requested_amount)}
                  </dd>
                </div>
                {loan.calculated_risk_score != null ? (
                  <div>
                    <dt className="text-gray-500">Risk score</dt>
                    <dd className="font-mono text-gray-900">
                      {loan.calculated_risk_score.toFixed(2)}
                    </dd>
                  </div>
                ) : null}
                {loan.transaction_reference ? (
                  <div className="sm:col-span-2">
                    <dt className="text-gray-500">CEFTS reference</dt>
                    <dd className="break-all font-mono text-xs text-gray-900">
                      {loan.transaction_reference}
                    </dd>
                  </div>
                ) : null}
                {loan.rejection_reason ? (
                  <div className="sm:col-span-2">
                    <dt className="text-gray-500">Reason</dt>
                    <dd className="text-red-800">{loan.rejection_reason}</dd>
                  </div>
                ) : null}
                {loan.repayment_reference ? (
                  <div className="sm:col-span-2">
                    <dt className="text-gray-500">Repayment reference</dt>
                    <dd className="break-all font-mono text-xs text-gray-900">
                      {loan.repayment_reference}
                    </dd>
                  </div>
                ) : null}
              </dl>

              {loan.status === "disbursed" ||
              loan.status === "repayment_pending" ||
              loan.status === "repaid" ? (
                <div className="mt-4">
                  <RepaymentPanel loan={loan} onRepaid={() => void refreshLoans()} />
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
