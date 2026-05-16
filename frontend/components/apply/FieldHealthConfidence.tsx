"use client";

import { assessFieldHealth, BAND_STYLES } from "@/lib/field-health";
import type { CropHealthMatrix } from "@/lib/supabase";

type Props = {
  cropHealthMatrix: CropHealthMatrix | Record<string, unknown> | null | undefined;
  calculatedRiskScore?: number | null;
  aiVerifiedAcreage?: number | null;
  declaredAcreage?: number | null;
};

export function FieldHealthConfidence({
  cropHealthMatrix,
  calculatedRiskScore = null,
  aiVerifiedAcreage = null,
  declaredAcreage = null,
}: Props) {
  const assessment = assessFieldHealth(cropHealthMatrix, calculatedRiskScore);
  if (!assessment) return null;

  const styles = BAND_STYLES[assessment.band];

  return (
    <div
      className={`mt-6 rounded-lg border px-4 py-4 text-sm ${styles.border} ${styles.bg} ${styles.text}`}
      role="status"
      aria-live="polite"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-semibold">Field health (AI photo review)</p>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${styles.badge}`}
        >
          {assessment.label}
        </span>
      </div>

      <p className="mt-2 leading-relaxed opacity-90">{assessment.summary}</p>

      <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-xs sm:grid-cols-3">
        <div>
          <dt className="opacity-70">Health score</dt>
          <dd className="font-mono font-semibold">{assessment.healthScore.toFixed(0)}/100</dd>
        </div>
        {assessment.canopyPercent != null && (
          <div>
            <dt className="opacity-70">Canopy cover</dt>
            <dd className="font-mono font-semibold">{assessment.canopyPercent.toFixed(0)}%</dd>
          </div>
        )}
        {assessment.vegetationIndex != null && (
          <div>
            <dt className="opacity-70">Green index (ExG)</dt>
            <dd className="font-mono font-semibold">
              {(assessment.vegetationIndex * 100).toFixed(0)}%
            </dd>
          </div>
        )}
        {assessment.imageQuality != null && (
          <div>
            <dt className="opacity-70">Photo quality</dt>
            <dd className="font-mono font-semibold">{assessment.imageQuality.toFixed(0)}/100</dd>
          </div>
        )}
        {assessment.cropMatch != null && (
          <div>
            <dt className="opacity-70">Crop match</dt>
            <dd className="font-mono font-semibold">
              {(assessment.cropMatch * 100).toFixed(0)}%
            </dd>
          </div>
        )}
        {aiVerifiedAcreage != null && (
          <div>
            <dt className="opacity-70">AI acreage</dt>
            <dd className="font-mono font-semibold">{aiVerifiedAcreage.toFixed(2)} ac</dd>
          </div>
        )}
        {declaredAcreage != null && aiVerifiedAcreage != null && (
          <div>
            <dt className="opacity-70">Declared acreage</dt>
            <dd className="font-mono font-semibold">{declaredAcreage.toFixed(2)} ac</dd>
          </div>
        )}
      </dl>

      {assessment.issues.length > 0 && (
        <p className="mt-3 text-xs">
          <span className="font-medium">Detected: </span>
          {assessment.issues.join(", ").replaceAll("_", " ")}
        </p>
      )}

      {assessment.diseaseDetected && assessment.issues.length === 0 && (
        <p className="mt-3 text-xs font-medium">Possible disease or stress flagged in imagery.</p>
      )}
    </div>
  );
}
