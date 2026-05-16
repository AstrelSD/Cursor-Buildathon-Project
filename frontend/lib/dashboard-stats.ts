import { loanDistrict, type LoanRow } from "./supabase";

const ACTIVE_STATUSES = new Set(["draft", "analyzing", "underwriting"]);

export type RegionalRisk = {
  district: string;
  count: number;
  avgRisk: number | null;
};

export type DashboardMetrics = {
  totalCapitalDeployedLkr: number;
  pipelineActive: number;
  approvalRate: number;
  regionalRisk: RegionalRisk[];
};

export function computeDashboardMetrics(loans: LoanRow[]): DashboardMetrics {
  const disbursed = loans.filter((l) => l.status === "disbursed");
  const decided = loans.filter((l) =>
    ["approved", "disbursed", "rejected"].includes(l.status),
  );
  const approved = loans.filter((l) =>
    ["approved", "disbursed"].includes(l.status),
  );

  const byDistrict = new Map<string, { count: number; riskSum: number; riskN: number }>();

  for (const loan of loans) {
    const district = loanDistrict(loan);
    const bucket = byDistrict.get(district) ?? { count: 0, riskSum: 0, riskN: 0 };
    bucket.count += 1;
    if (loan.calculated_risk_score != null) {
      bucket.riskSum += loan.calculated_risk_score;
      bucket.riskN += 1;
    }
    byDistrict.set(district, bucket);
  }

  const regionalRisk: RegionalRisk[] = [...byDistrict.entries()]
    .map(([district, v]) => ({
      district,
      count: v.count,
      avgRisk: v.riskN > 0 ? v.riskSum / v.riskN : null,
    }))
    .sort((a, b) => b.count - a.count);

  return {
    totalCapitalDeployedLkr: disbursed.reduce((s, l) => s + Number(l.requested_amount), 0),
    pipelineActive: loans.filter((l) => ACTIVE_STATUSES.has(l.status)).length,
    approvalRate: decided.length > 0 ? (approved.length / decided.length) * 100 : 0,
    regionalRisk,
  };
}

export function formatLkr(amount: number): string {
  return new Intl.NumberFormat("en-LK", {
    style: "currency",
    currency: "LKR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function statusBadgeClass(status: string): string {
  switch (status) {
    case "disbursed":
      return "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30";
    case "approved":
      return "bg-sky-500/15 text-sky-300 ring-sky-500/30";
    case "rejected":
      return "bg-rose-500/15 text-rose-300 ring-rose-500/30";
    case "analyzing":
    case "underwriting":
      return "bg-amber-500/15 text-amber-200 ring-amber-500/30";
    default:
      return "bg-zinc-500/15 text-zinc-300 ring-zinc-500/30";
  }
}
