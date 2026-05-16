import { getApiBaseUrl } from "./api";

export type VoiceIntakeResult = {
  status: string;
  loan_id: string;
  crop_type: string;
  declared_acreage: number;
  requested_amount: number;
};

async function parseError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    if (typeof body.detail === "string") return body.detail;
  } catch {
    /* ignore */
  }
  return response.statusText || `Request failed (${response.status})`;
}

export async function fetchVoiceSignedUrl(): Promise<string> {
  const response = await fetch(`${getApiBaseUrl()}/api/voice/signed-url`);
  if (!response.ok) throw new Error(await parseError(response));
  const body = (await response.json()) as { signed_url: string };
  return body.signed_url;
}

export async function submitVoiceIntake(
  transcript: string,
  userId?: string,
): Promise<VoiceIntakeResult> {
  const response = await fetch(`${getApiBaseUrl()}/api/voice/intake`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      transcript,
      ...(userId ? { user_id: userId } : {}),
    }),
  });
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<VoiceIntakeResult>;
}

export function getPublicAgentId(): string | undefined {
  const id = process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID?.trim();
  return id || undefined;
}

export async function fetchVoiceConfig(): Promise<{
  elevenlabs_configured: boolean;
  agent_configured: boolean;
}> {
  const response = await fetch(`${getApiBaseUrl()}/api/voice/config`);
  if (!response.ok) throw new Error(await parseError(response));
  return response.json() as Promise<{
    elevenlabs_configured: boolean;
    agent_configured: boolean;
  }>;
}
