import type { CropHealthMatrix } from "@/lib/supabase";
import {
  HIGH_CROP_MATCH_CONFIDENCE,
  HIGH_HEALTH_SCORE,
  HIGH_IMAGE_QUALITY_SCORE,
  MIN_CROP_MATCH_CONFIDENCE,
  MIN_HEALTH_SCORE,
  MIN_IMAGE_QUALITY_SCORE,
  RISK_SCORE_HIGH_BAND,
  RISK_SCORE_LOW_BAND,
} from "@/lib/field-health-thresholds";

export type FieldHealthBand = "high" | "medium" | "low";

export type FieldHealthAssessment = {
  band: FieldHealthBand;
  label: string;
  summary: string;
  healthScore: number;
  canopyPercent: number | null;
  vegetationIndex: number | null;
  imageQuality: number | null;
  cropMatch: number | null;
  issues: string[];
  diseaseDetected: boolean;
};

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((item): item is string => typeof item === "string");
}

/** Map vision agent output to High / Medium / Low field-health confidence. */
export function assessFieldHealth(
  matrix: CropHealthMatrix | Record<string, unknown> | null | undefined,
  calculatedRiskScore: number | null = null,
): FieldHealthAssessment | null {
  if (!matrix) return null;

  const healthScore = asNumber(matrix.health_score);
  if (healthScore == null) return null;

  const canopyPercent = asNumber(matrix.canopy_cover_percent);
  const vegetationIndex = asNumber(matrix.vegetation_index);
  const imageQuality = asNumber(matrix.image_quality_score);
  const cropMatch = asNumber(matrix.crop_match_confidence);
  const diseaseDetected = Boolean(matrix.anomaly_flag ?? matrix.disease_detected);
  const issues = asStringArray(matrix.detected_issues);

  let band: FieldHealthBand = "medium";

  const lowSignals =
    healthScore < MIN_HEALTH_SCORE ||
    diseaseDetected ||
    (imageQuality != null && imageQuality < MIN_IMAGE_QUALITY_SCORE) ||
    (cropMatch != null && cropMatch < MIN_CROP_MATCH_CONFIDENCE) ||
    (calculatedRiskScore != null && calculatedRiskScore > RISK_SCORE_LOW_BAND);

  const highSignals =
    healthScore >= HIGH_HEALTH_SCORE &&
    !diseaseDetected &&
    issues.length === 0 &&
    (imageQuality == null || imageQuality >= HIGH_IMAGE_QUALITY_SCORE) &&
    (cropMatch == null || cropMatch >= HIGH_CROP_MATCH_CONFIDENCE) &&
    (calculatedRiskScore == null || calculatedRiskScore <= RISK_SCORE_HIGH_BAND);

  if (lowSignals) {
    band = "low";
  } else if (highSignals) {
    band = "high";
  } else {
    band = "medium";
  }

  const label =
    band === "high" ? "High confidence" : band === "medium" ? "Medium confidence" : "Low confidence";

  const summary =
    band === "high"
      ? "Field imagery shows strong canopy vigor with no major stress signals."
      : band === "medium"
        ? "Field looks workable; some stress or uncertainty was detected — underwriting will weigh these signals in the risk score."
        : "Field health or photo quality does not meet underwriting standards. A loan in this band will not be approved until you submit a clearer photo.";

  return {
    band,
    label,
    summary,
    healthScore,
    canopyPercent,
    vegetationIndex,
    imageQuality,
    cropMatch,
    issues,
    diseaseDetected,
  };
}

export const BAND_STYLES: Record<
  FieldHealthBand,
  { border: string; bg: string; text: string; badge: string }
> = {
  high: {
    border: "border-green-200",
    bg: "bg-green-50",
    text: "text-green-900",
    badge: "bg-green-600 text-white",
  },
  medium: {
    border: "border-amber-200",
    bg: "bg-amber-50",
    text: "text-amber-950",
    badge: "bg-amber-500 text-white",
  },
  low: {
    border: "border-red-200",
    bg: "bg-red-50",
    text: "text-red-900",
    badge: "bg-red-600 text-white",
  },
};
