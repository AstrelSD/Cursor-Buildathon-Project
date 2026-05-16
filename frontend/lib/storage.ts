import { getApiBaseUrl } from "./api";

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    /* ignore */
  }
  return response.statusText || `Upload failed (${response.status})`;
}

/** Upload via backend (uses service role — no browser Supabase key required). */
export async function uploadCropEvidence(
  loanId: string,
  file: File,
): Promise<string> {
  const form = new FormData();
  form.append("file", file);

  const response = await fetch(
    `${getApiBaseUrl()}/api/loans/${loanId}/evidence/upload`,
    { method: "POST", body: form },
  );

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  const body = (await response.json()) as { multimodal_evidence_url: string };
  return body.multimodal_evidence_url;
}
