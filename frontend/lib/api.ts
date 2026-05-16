import type { LoanRow } from "@/lib/supabase";

const DEFAULT_API_URL = "http://localhost:8000";

export function getApiBaseUrl(): string {
  return (process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_URL).replace(/\/$/, "");
}

export type CreateLoanPayload = {
  crop_type: string;
  declared_acreage: number;
  requested_amount: number;
  user_id?: string;
};

export type CreateLoanResponse = {
  status: string;
  loan_id: string;
};

export type LoanStatusResponse = {
  id: string;
  status: string;
  crop_type: string;
  declared_acreage: number;
  requested_amount: number;
  calculated_risk_score: number | null;
  rejection_reason: string | null;
  transaction_reference: string | null;
  multimodal_evidence_url: string | null;
  ai_verified_acreage: number | null;
  crop_health_matrix: Record<string, unknown> | null;
};

export type AccountBalanceResponse = {
  account_number: string;
  available_balance: string | null;
  ledger_balance: string | null;
  currency: string | null;
  transaction_reference: string;
  banking_mode: "mock" | "live" | string;
};

export type RepaymentQrResponse = {
  transaction_reference: string;
  request_ref_no: string;
  qr_code: string;
  response_code: string;
  response_description: string;
  banking_mode: string;
};

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string | { msg?: string }[] };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail.map((d) => d.msg ?? JSON.stringify(d)).join("; ");
    }
  } catch {
    /* ignore */
  }
  return response.statusText || `Request failed (${response.status})`;
}

export async function createLoan(
  payload: CreateLoanPayload,
): Promise<CreateLoanResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/loans`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<CreateLoanResponse>;
}

export async function evaluateLoan(loanId: string): Promise<void> {
  const response = await fetch(`${getApiBaseUrl()}/api/loans/${loanId}/evaluate`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(await parseError(response));
}

export async function fetchLoanStatus(loanId: string): Promise<LoanStatusResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/loans/${loanId}`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<LoanStatusResponse>;
}

export async function fetchUserLoans(userId: string): Promise<LoanRow[]> {
  const params = new URLSearchParams({ user_id: userId });
  const response = await fetch(`${getApiBaseUrl()}/api/loans?${params}`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<LoanRow[]>;
}

export async function fetchPayoutAccountBalance(): Promise<AccountBalanceResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/loans/banking/payout-balance`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<AccountBalanceResponse>;
}

export type RepaymentCeftsResponse = {
  transaction_reference: string;
  banking_mode: string;
  source_account: string;
  source_bank_code: string;
  destination_account: string;
  destination_bank_code: string;
  amount: number;
  status: string;
};

export type RepaymentStatusResponse = {
  paid: boolean;
  detection_method: string | null;
  matched_reference: string | null;
  banking_mode: string;
  message: string;
  loan_status: string;
};

export async function fetchRepaymentQr(loanId: string): Promise<RepaymentQrResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/loans/${loanId}/repayment/qr`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<RepaymentQrResponse>;
}

export async function initiateRepaymentCefts(
  loanId: string,
): Promise<RepaymentCeftsResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/loans/${loanId}/repayment/cefts`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<RepaymentCeftsResponse>;
}

export async function fetchRepaymentStatus(
  loanId: string,
): Promise<RepaymentStatusResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/loans/${loanId}/repayment/status`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<RepaymentStatusResponse>;
}
