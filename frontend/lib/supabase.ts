import { createClient, type SupabaseClient } from "@supabase/supabase-js";

export type LoanStatus =
  | "draft"
  | "analyzing"
  | "underwriting"
  | "approved"
  | "disbursed"
  | "repayment_pending"
  | "repaid"
  | "rejected";

export type CropHealthMatrix = {
  chlorophyll_index?: number;
  vegetation_index?: number;
  anomaly_flag?: boolean;
  disease_detected?: boolean;
  classification?: string;
  health_score?: number;
  image_quality_score?: number;
  crop_match_confidence?: number;
  canopy_cover_percent?: number;
  detected_issues?: string[];
  growth_stage?: string;
  acreage_confidence?: number;
};

export type LoanRow = {
  id: string;
  user_id: string;
  crop_type: string;
  declared_acreage: number;
  requested_amount: number;
  ai_verified_acreage: number | null;
  crop_health_matrix: CropHealthMatrix | null;
  market_volatility_index: number | null;
  calculated_risk_score: number | null;
  rejection_reason: string | null;
  status: LoanStatus;
  multimodal_evidence_url: string | null;
  transaction_reference: string | null;
  repayment_method: "qr" | "cefts" | null;
  repayment_reference: string | null;
  repayment_qr_request_ref: string | null;
  repaid_at: string | null;
  created_at: string;
  profiles:
    | {
        district: string;
        payout_account_number: string | null;
        payout_bank_code: string | null;
      }
    | {
        district: string;
        payout_account_number: string | null;
        payout_bank_code: string | null;
      }[]
    | null;
};

export type ProfilePayout = {
  payout_account_number: string | null;
  payout_bank_code: string | null;
};

export function getSupabase(): SupabaseClient {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!url || !key) {
    throw new Error(
      "Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY.",
    );
  }

  return createClient(url, key);
}

export function loanDistrict(loan: LoanRow): string {
  const profile = loan.profiles;
  if (!profile) return "Unknown";
  if (Array.isArray(profile)) return profile[0]?.district ?? "Unknown";
  return profile.district ?? "Unknown";
}
