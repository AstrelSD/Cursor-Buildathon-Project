"use client";

import Link from "next/link";
import {
  ArrowRight,
  Check,
  Loader2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { MultimodalUploader } from "@/components/MultimodalUploader";
import { RealtimeVoiceConsole } from "@/components/RealtimeVoiceConsole";
import { useAuth } from "@/components/providers/AuthProvider";
import { PATH_LOGIN, PATH_REGISTER } from "@/constants/routes";
import type { VoiceIntakeResult } from "@/lib/voice";
import {
  createLoan,
  evaluateLoan,
  fetchLoanStatus,
  type LoanStatusResponse,
} from "@/lib/api";
import type { LoanStatus } from "@/lib/supabase";
import { uploadCropEvidence } from "@/lib/storage";

import { FieldHealthConfidence } from "@/components/apply/FieldHealthConfidence";
import { CROP_OPTIONS } from "@/constants/crops";
import type { CropHealthMatrix } from "@/lib/supabase";

type Step = {
  id: number;
  title: string;
  status: string;
  done: boolean;
};

function buildSteps(
  intakeComplete: boolean,
  formComplete: boolean,
  phase: "idle" | "submitting" | "analyzing" | "done",
  loan: LoanStatusResponse | null,
): Step[] {
  const status = loan?.status;

  return [
    {
      id: 1,
      title: "Listening to your needs",
      status: intakeComplete
        ? "Application details captured"
        : "Speak or enter crop and loan details",
      done: intakeComplete,
    },
    {
      id: 2,
      title: "Reviewing farm photos",
      status:
        phase === "submitting"
          ? "Uploading evidence…"
          : status === "analyzing" || status === "underwriting"
            ? "AI agents analyzing your field…"
            : loan?.multimodal_evidence_url
              ? "Evidence attached"
              : "Waiting for upload…",
      done:
        Boolean(loan?.multimodal_evidence_url) ||
        status === "analyzing" ||
        status === "underwriting" ||
        status === "approved" ||
        status === "disbursed" ||
        status === "rejected",
    },
    {
      id: 3,
      title: "Finalizing your loan offer",
      status:
        status === "disbursed"
          ? `Approved & disbursed · Ref ${loan?.transaction_reference ?? "—"}`
          : status === "approved"
            ? "Approved — processing disbursement…"
            : status === "rejected"
              ? (loan?.rejection_reason ?? "Application declined")
              : phase === "analyzing" || status === "underwriting"
                ? "Underwriter calculating risk…"
                : "Pending",
      done: status === "approved" || status === "disbursed" || status === "rejected",
    },
  ];
}

function decisionLabel(status: LoanStatus | undefined): {
  tone: "success" | "error" | "neutral";
  title: string;
  detail: string;
} | null {
  if (!status) return null;
  if (status === "rejected") {
    return { tone: "error", title: "Not approved", detail: "See reason below." };
  }
  if (status === "disbursed" || status === "approved") {
    return { tone: "success", title: "Approved", detail: "Your application passed AI underwriting." };
  }
  return null;
}

export function ApplyPageClient() {
  const { session, isLoading, isAuthenticated } = useAuth();
  const profileUserId = session?.user?.id;

  const [cropType, setCropType] = useState<string>(CROP_OPTIONS[0]);
  const [acreage, setAcreage] = useState("2.5");
  const [amount, setAmount] = useState("75000");
  const [file, setFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [loanId, setLoanId] = useState<string | null>(null);
  const [loan, setLoan] = useState<LoanStatusResponse | null>(null);
  const [phase, setPhase] = useState<"idle" | "submitting" | "analyzing" | "done">("idle");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [voiceIntakeDone, setVoiceIntakeDone] = useState(false);

  const formComplete =
    cropType.length > 0 &&
    Number(acreage) > 0 &&
    Number(amount) >= 5000 &&
    file !== null;

  const intakeComplete = voiceIntakeDone || Boolean(loanId);

  const steps = useMemo(
    () => buildSteps(intakeComplete, formComplete, phase, loan),
    [intakeComplete, formComplete, phase, loan],
  );

  const handleVoiceIntake = useCallback((payload: VoiceIntakeResult) => {
    setCropType(payload.crop_type);
    setAcreage(String(payload.declared_acreage));
    setAmount(String(payload.requested_amount));
    setLoanId(payload.loan_id);
    setVoiceIntakeDone(true);
    setSubmitError(null);
  }, []);

  const decision = decisionLabel(loan?.status as LoanStatus | undefined);

  const previewUrl = useMemo(
    () => (file ? URL.createObjectURL(file) : null),
    [file],
  );

  useEffect(() => {
    if (!previewUrl) return;
    return () => URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  useEffect(() => {
    if (!loanId || phase !== "analyzing") return;

    let cancelled = false;

    async function poll() {
      try {
        const row = await fetchLoanStatus(loanId!);
        if (cancelled) return;
        setLoan(row);
        if (
          row.status === "approved" ||
          row.status === "disbursed" ||
          row.status === "rejected"
        ) {
          setPhase("done");
        }
      } catch {
        /* keep polling */
      }
    }

    void poll();
    const interval = setInterval(() => void poll(), 2000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [loanId, phase]);

  const handleFileSelect = useCallback((next: File | null) => {
    setFile(next);
    setUploadError(null);
    if (!next) return;
    if (!next.type.startsWith("image/")) {
      setUploadError("Please choose a JPEG, PNG, or WebP image.");
      setFile(null);
      return;
    }
    if (next.size > 10 * 1024 * 1024) {
      setUploadError("Image must be 10 MB or smaller.");
      setFile(null);
    }
  }, []);

  async function handleSubmit() {
    if (!profileUserId || !file || !formComplete) return;

    setSubmitError(null);
    setUploadError(null);
    setPhase("submitting");

    try {
      let id = loanId;
      if (!id) {
        const created = await createLoan({
          crop_type: cropType,
          declared_acreage: Number(acreage),
          requested_amount: Number(amount),
          user_id: profileUserId,
        });
        id = created.loan_id;
        setLoanId(id);
      }

      const objectPath = await uploadCropEvidence(id, file);
      setLoan((prev) =>
        prev
          ? { ...prev, multimodal_evidence_url: objectPath }
          : {
              id,
              status: "draft",
              crop_type: cropType,
              declared_acreage: Number(acreage),
              requested_amount: Number(amount),
              calculated_risk_score: null,
              rejection_reason: null,
              transaction_reference: null,
              multimodal_evidence_url: objectPath,
              ai_verified_acreage: null,
              crop_health_matrix: null,
            },
      );

      await evaluateLoan(id);
      setPhase("analyzing");
    } catch (e) {
      const message = e instanceof Error ? e.message : "Submission failed.";
      setSubmitError(message);
      setPhase("idle");
    }
  }

  const isBusy = phase === "submitting" || phase === "analyzing";

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center py-16 text-sm text-gray-500">
        Loading…
      </div>
    );
  }

  if (!isAuthenticated || !profileUserId) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center px-4 py-16 text-center">
        <p className="max-w-md text-lg font-semibold text-gray-900">
          Log in to apply for a farm loan
        </p>
        <p className="mt-2 max-w-sm text-sm text-gray-600">
          Registration includes your district and phone so we can underwrite your
          application.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link
            href={PATH_LOGIN}
            className="rounded-full bg-[#2E7D32] px-6 py-2.5 text-sm font-medium text-white hover:bg-[#1b5e20]"
          >
            Log in
          </Link>
          <Link
            href={PATH_REGISTER}
            className="rounded-full border border-[#2E7D32] px-6 py-2.5 text-sm font-medium text-[#2E7D32] hover:bg-[#2E7D32]/5"
          >
            Register
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col items-center bg-[#f8faf8] px-4 py-8 sm:px-6">
      <div className="relative w-full max-w-5xl rounded-2xl border border-gray-100 bg-white shadow-xl">
        <Link
          href="/"
          className="absolute right-4 top-4 rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 sm:right-6 sm:top-6"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </Link>

        <header className="border-b border-gray-100 px-6 pb-6 pt-8 sm:px-10 sm:pt-10">
          <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
            Apply for a Farm Loan
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-gray-600 sm:text-base">
            Enter your crop details, upload a field photo, and our AI agents will
            review your application in seconds.
          </p>
        </header>

        <div className="grid gap-8 p-6 sm:p-10 lg:grid-cols-2">
          <div className="space-y-6">
            <section className="rounded-xl border border-gray-100 bg-gray-50/50 p-6">
              <h2 className="text-sm font-semibold text-gray-900">
                Tell us what you need
              </h2>
              <div className="mt-4">
                <RealtimeVoiceConsole
                  disabled={isBusy}
                  profileUserId={profileUserId}
                  onIntakeComplete={handleVoiceIntake}
                  onError={setSubmitError}
                />
              </div>

              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="crop" className="mb-1 block text-sm font-medium text-gray-700">
                    Crop type
                  </label>
                  <select
                    id="crop"
                    value={cropType}
                    disabled={isBusy}
                    onChange={(e) => setCropType(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-gray-900 outline-none focus:border-[#2E7D32] focus:ring-2 focus:ring-[#2E7D32]/20"
                  >
                    {CROP_OPTIONS.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="acreage" className="mb-1 block text-sm font-medium text-gray-700">
                    Declared acreage
                  </label>
                  <input
                    id="acreage"
                    type="number"
                    min="0.1"
                    step="0.1"
                    value={acreage}
                    disabled={isBusy}
                    onChange={(e) => setAcreage(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 px-3 py-2.5 outline-none focus:border-[#2E7D32] focus:ring-2 focus:ring-[#2E7D32]/20"
                  />
                </div>
                <div>
                  <label htmlFor="amount" className="mb-1 block text-sm font-medium text-gray-700">
                    Requested amount (LKR)
                  </label>
                  <input
                    id="amount"
                    type="number"
                    min="5000"
                    step="500"
                    value={amount}
                    disabled={isBusy}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 px-3 py-2.5 outline-none focus:border-[#2E7D32] focus:ring-2 focus:ring-[#2E7D32]/20"
                  />
                </div>
              </div>
            </section>

            <section className="rounded-xl border border-gray-100 p-6">
              <h2 className="text-sm font-semibold text-gray-900">
                Add Photos or Documents
              </h2>
              <div className="mt-4">
                <MultimodalUploader
                  file={file}
                  previewUrl={previewUrl}
                  disabled={isBusy}
                  onFileSelect={handleFileSelect}
                  onValidationError={setUploadError}
                  error={uploadError}
                />
                <p className="mt-3 text-xs leading-relaxed text-gray-500">
                  For best AI review: daylight, full field in frame, match your selected crop,
                  avoid blur or heavy shadows. We analyze canopy health, disease cues, and acreage.
                </p>
              </div>
            </section>
          </div>

          <div className="flex flex-col">
            <section className="flex-1 rounded-xl border border-gray-100 p-6">
              <h2 className="text-sm font-semibold text-gray-900">
                Application Status
              </h2>
              <ol className="mt-6 space-y-6">
                {steps.map((step) => (
                  <li key={step.id} className="flex gap-4">
                    {step.done ? (
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#4CAF50] text-white">
                        <Check className="h-4 w-4" strokeWidth={3} />
                      </span>
                    ) : phase === "analyzing" && step.id === 2 ? (
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-[#4CAF50]">
                        <Loader2 className="h-4 w-4 animate-spin text-[#2E7D32]" />
                      </span>
                    ) : (
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-gray-200 text-sm font-semibold text-gray-400">
                        {step.id}
                      </span>
                    )}
                    <div>
                      <p
                        className={
                          step.done
                            ? "font-medium text-[#2E7D32]"
                            : "font-medium text-gray-500"
                        }
                      >
                        {step.title}
                      </p>
                      <p className="mt-0.5 text-sm text-gray-400">{step.status}</p>
                    </div>
                  </li>
                ))}
              </ol>

              {loan?.crop_health_matrix && (
                <FieldHealthConfidence
                  cropHealthMatrix={loan.crop_health_matrix as CropHealthMatrix}
                  calculatedRiskScore={loan.calculated_risk_score}
                  aiVerifiedAcreage={loan.ai_verified_acreage}
                  declaredAcreage={loan.declared_acreage}
                />
              )}

              {decision && loan && (
                <div
                  className={`mt-6 rounded-lg border px-4 py-3 text-sm ${
                    decision.tone === "success"
                      ? "border-green-200 bg-green-50 text-green-900"
                      : decision.tone === "error"
                        ? "border-red-200 bg-red-50 text-red-900"
                        : "border-gray-200 bg-gray-50"
                  }`}
                >
                  <p className="font-semibold">{decision.title}</p>
                  {loan.calculated_risk_score != null && (
                    <p className="mt-1">
                      Risk score:{" "}
                      <span className="font-mono">{loan.calculated_risk_score.toFixed(2)}</span>
                    </p>
                  )}
                  {loan.rejection_reason && (
                    <p className="mt-1 text-red-800">{loan.rejection_reason}</p>
                  )}
                  {loan.transaction_reference && (
                    <p className="mt-1 font-mono text-xs">
                      Ref: {loan.transaction_reference}
                    </p>
                  )}
                </div>
              )}
            </section>

            <div className="mt-6 lg:mt-8">
              {submitError && (
                <p className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
                  {submitError}
                </p>
              )}
              <button
                type="button"
                disabled={!formComplete || isBusy}
                onClick={() => void handleSubmit()}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#2E7D32] py-3.5 text-base font-medium text-white transition-colors hover:bg-[#1b5e20] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {phase === "submitting" ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Submitting…
                  </>
                ) : phase === "analyzing" ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    AI review in progress…
                  </>
                ) : (
                  <>
                    Submit Application
                    <ArrowRight className="h-5 w-5" />
                  </>
                )}
              </button>
              <p className="mt-3 text-center text-xs text-gray-400">
                Uploads to Supabase Storage, then runs vision + market + underwriter agents.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
