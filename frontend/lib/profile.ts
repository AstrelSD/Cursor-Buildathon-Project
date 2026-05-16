import { getApiBaseUrl } from "@/lib/api";
import type { ProfilePayout } from "@/lib/supabase";

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    if (typeof body.detail === "string" && body.detail.length > 0) {
      return body.detail;
    }
  } catch {
    /* ignore */
  }
  if (response.status === 0 || response.type === "error") {
    return `Cannot reach API at ${getApiBaseUrl()}. Start the backend (uvicorn) and try again.`;
  }
  return response.statusText || `Request failed (${response.status})`;
}

export async function fetchProfilePayout(userId: string): Promise<ProfilePayout> {
  const params = new URLSearchParams({ user_id: userId });
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}/api/profile/payout?${params}`);
  } catch {
    throw new Error(
      `Cannot reach API at ${getApiBaseUrl()}. Start the backend and refresh the page.`,
    );
  }
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<ProfilePayout>;
}

export async function updateProfilePayout(
  userId: string,
  payout: ProfilePayout,
): Promise<ProfilePayout> {
  let response: Response;
  try {
    response = await fetch(`${getApiBaseUrl()}/api/profile/payout`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        payout_account_number: payout.payout_account_number,
        payout_bank_code: payout.payout_bank_code,
      }),
    });
  } catch {
    throw new Error(
      `Cannot reach API at ${getApiBaseUrl()}. Start the backend, then save again.`,
    );
  }
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<ProfilePayout>;
}
