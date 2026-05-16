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
  ai_verified_acreage: number | null;
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
