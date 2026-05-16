"use client";

import { useCallback, useEffect, useState } from "react";

import { UnderwritingTerminal } from "@/components/UnderwritingTerminal";
import {
  computeDashboardMetrics,
  formatLkr,
  statusBadgeClass,
  type DashboardMetrics,
} from "@/lib/dashboard-stats";
import { getSupabase, loanDistrict, type LoanRow } from "@/lib/supabase";

const LOAN_SELECT =
  "id, user_id, crop_type, declared_acreage, requested_amount, ai_verified_acreage, crop_health_matrix, market_volatility_index, calculated_risk_score, rejection_reason, status, multimodal_evidence_url, transaction_reference, created_at, profiles(district)";

export function AgriLendDashboard() {
  const [loans, setLoans] = useState<LoanRow[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const supabase = getSupabase();
      const { data, error: queryError } = await supabase
        .from("loans")
        .select(LOAN_SELECT)
        .order("created_at", { ascending: false });

      if (queryError) throw queryError;
      const rows = (data ?? []) as LoanRow[];
      setLoans(rows);
      setMetrics(computeDashboardMetrics(rows));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load loans.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();

    try {
      const supabase = getSupabase();
      const channel = supabase
        .channel("loans-dashboard-ledger")
        .on(
          "postgres_changes",
          { event: "*", schema: "public", table: "loans" },
          () => {
            void refresh();
          },
        )
        .subscribe();

      return () => {
        void supabase.removeChannel(channel);
      };
    } catch {
      return undefined;
    }
  }, [refresh]);

  return (
    <div className="min-h-full bg-[#050b08] text-zinc-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(ellipse_at_top,_rgba(16,185,129,0.12),_transparent_55%)]" />
      <div className="relative mx-auto flex max-w-7xl flex-col gap-8 px-4 py-10 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-500/80">
              Agri-Lend · Sri Lanka
            </p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
              Executive Risk Console
            </h1>
            <p className="mt-2 max-w-xl text-sm text-zinc-400">
              Live multi-agent underwriting ledger. Trigger evaluation via API while this
              terminal streams agent state from Supabase Realtime.
            </p>
          </div>
          <div className="flex gap-3">
            <a
              href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/docs`}
              target="_blank"
              rel="noreferrer"
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-200 backdrop-blur hover:bg-white/10"
            >
              API Docs
            </a>
            <button
              type="button"
              onClick={() => void refresh()}
              className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500"
            >
              Refresh
            </button>
          </div>
        </header>

        {error && (
          <div className="rounded-xl border border-rose-500/30 bg-rose-950/40 px-4 py-3 text-sm text-rose-200">
            {error}
            <p className="mt-1 text-xs text-rose-300/80">
              Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY, then run the
              realtime migration in Supabase.
            </p>
          </div>
        )}

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            label="Total Capital Deployed"
            value={loading ? "…" : formatLkr(metrics?.totalCapitalDeployedLkr ?? 0)}
            hint="Disbursed principal (LKR)"
          />
          <MetricCard
            label="Pipeline Active"
            value={loading ? "…" : String(metrics?.pipelineActive ?? 0)}
            hint="draft · analyzing · underwriting"
          />
          <MetricCard
            label="Approval Rate"
            value={loading ? "…" : `${(metrics?.approvalRate ?? 0).toFixed(0)}%`}
            hint="Approved vs decided applications"
          />
          <MetricCard
            label="Ledger Records"
            value={loading ? "…" : String(loans.length)}
            hint="All loans in Supabase"
          />
        </section>

        <section className="grid gap-6 lg:grid-cols-5">
          <div className="lg:col-span-2">
            <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-zinc-400">
              Regional Risk Breakdown
            </h2>
            <div className="space-y-2 rounded-2xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-xl">
              {(metrics?.regionalRisk ?? []).length === 0 && !loading && (
                <p className="text-sm text-zinc-500">No regional data yet.</p>
              )}
              {(metrics?.regionalRisk ?? []).map((row) => (
                <div
                  key={row.district}
                  className="flex items-center justify-between gap-4 rounded-lg bg-black/20 px-3 py-2"
                >
                  <span className="text-sm text-zinc-200">{row.district}</span>
                  <span className="text-xs text-zinc-500">{row.count} loans</span>
                  <span className="font-mono text-sm text-emerald-400/90">
                    {row.avgRisk != null ? row.avgRisk.toFixed(1) : "—"}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <UnderwritingTerminal className="lg:col-span-3" initialLoans={loans} />
        </section>

        <section>
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wider text-zinc-400">
            Underwriting Ledger
          </h2>
          <div className="overflow-hidden rounded-2xl border border-white/10 bg-white/[0.02] backdrop-blur-xl">
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-white/10 bg-black/30 text-xs uppercase tracking-wider text-zinc-500">
                  <tr>
                    <th className="px-4 py-3">Crop</th>
                    <th className="px-4 py-3">District</th>
                    <th className="px-4 py-3">Amount</th>
                    <th className="px-4 py-3">Risk</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Reference</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-zinc-500">
                        Loading ledger…
                      </td>
                    </tr>
                  )}
                  {!loading && loans.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-8 text-center text-zinc-500">
                        No loans yet. Create a row in Supabase and POST evaluate to see
                        live updates.
                      </td>
                    </tr>
                  )}
                  {loans.map((loan) => (
                    <tr
                      key={loan.id}
                      className="border-b border-white/5 hover:bg-white/[0.03]"
                    >
                      <td className="px-4 py-3 font-medium text-zinc-100">
                        {loan.crop_type}
                        <span className="mt-0.5 block font-mono text-[10px] text-zinc-600">
                          {loan.id.slice(0, 8)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-zinc-400">{loanDistrict(loan)}</td>
                      <td className="px-4 py-3">{formatLkr(Number(loan.requested_amount))}</td>
                      <td className="px-4 py-3 font-mono text-emerald-400/90">
                        {loan.calculated_risk_score != null
                          ? loan.calculated_risk_score.toFixed(1)
                          : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${statusBadgeClass(loan.status)}`}
                        >
                          {loan.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-zinc-500">
                        {loan.transaction_reference ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 shadow-lg backdrop-blur-xl">
      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
      <p className="mt-1 text-xs text-zinc-500">{hint}</p>
    </div>
  );
}
