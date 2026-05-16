import type { CropHealthMatrix } from "@/lib/supabase";

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
    healthScore < 45 ||
    diseaseDetected ||
    (imageQuality != null && imageQuality < 40) ||
    (cropMatch != null && cropMatch < 0.4) ||
    (calculatedRiskScore != null && calculatedRiskScore > 55);

  const highSignals =
    healthScore >= 72 &&
    !diseaseDetected &&
    issues.length === 0 &&
    (imageQuality == null || imageQuality >= 58) &&
    (cropMatch == null || cropMatch >= 0.65) &&
    (calculatedRiskScore == null || calculatedRiskScore <= 38);

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
        ? "Field looks workable; some stress or uncertainty was detected — review details below."
        : "Field health or photo quality raises concern; underwriting may decline or request a new photo.";

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
