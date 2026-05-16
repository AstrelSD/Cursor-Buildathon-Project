import type { LoanRow } from "./supabase";

export type TerminalLogLevel = "info" | "success" | "warn" | "error";

export type TerminalLogEntry = {
  id: string;
  at: string;
  level: TerminalLogLevel;
  message: string;
  loanId?: string;
};

function ts(): string {
  return new Date().toISOString().slice(11, 23);
}

export function logsFromLoanTransition(
  previous: LoanRow | null,
  current: LoanRow,
): TerminalLogEntry[] {
  const entries: TerminalLogEntry[] = [];
  const loanId = current.id;
  const base = `${loanId.slice(0, 8)}`;

  if (!previous || previous.status !== current.status) {
    switch (current.status) {
      case "analyzing":
        entries.push({
          id: `${loanId}-analyzing`,
          at: ts(),
          level: "info",
          loanId,
          message: `[PROCESSING] Vision Agent processing spatial field matrices for ${current.crop_type} (${base})…`,
        });
        break;
      case "underwriting":
        entries.push({
          id: `${loanId}-underwriting`,
          at: ts(),
          level: "info",
          loanId,
          message: `[PROCESSING] Quant Underwriter synthesizing risk vectors for ${base}…`,
        });
        break;
      case "approved":
        entries.push({
          id: `${loanId}-approved`,
          at: ts(),
          level: "success",
          loanId,
          message: `[PASSED] Underwriter verification confirmed. Risk score ${formatScore(current.calculated_risk_score)}.`,
        });
        break;
      case "disbursed":
        entries.push({
          id: `${loanId}-disbursed`,
          at: ts(),
          level: "success",
          loanId,
          message: `[PASSED] Bank wire sequence complete. Ref ${current.transaction_reference ?? "pending"}.`,
        });
        break;
      case "rejected":
        entries.push({
          id: `${loanId}-rejected`,
          at: ts(),
          level: "error",
          loanId,
          message: `[FAILED] ${current.rejection_reason ?? "Application rejected."}`,
        });
        break;
      default:
        break;
    }
  }

  if (
    current.crop_health_matrix &&
    (!previous?.crop_health_matrix ||
      JSON.stringify(previous.crop_health_matrix) !==
        JSON.stringify(current.crop_health_matrix))
  ) {
    const health = current.crop_health_matrix.health_score;
    entries.push({
      id: `${loanId}-vision`,
      at: ts(),
      level: "success",
      loanId,
      message: `[PASSED] Vision agronomist: health ${health ?? "—"}, acreage ${current.ai_verified_acreage ?? "—"}.`,
    });
  }

  if (
    current.market_volatility_index != null &&
    previous?.market_volatility_index !== current.market_volatility_index
  ) {
    entries.push({
      id: `${loanId}-market`,
      at: ts(),
      level: "success",
      loanId,
      message: `[PASSED] Market RAG: volatility index ${current.market_volatility_index.toFixed(2)}.`,
    });
  }

  return entries;
}

function formatScore(score: number | null): string {
  if (score == null) return "—";
  return score.toFixed(2);
}

export function seedLog(): TerminalLogEntry {
  return {
    id: "boot",
    at: ts(),
    level: "info",
    message: "[READY] Underwriting terminal listening on public.loans realtime channel…",
  };
}
