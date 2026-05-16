"use client";

import {
  ConversationProvider,
  useConversation,
  useConversationControls,
  useConversationStatus,
} from "@elevenlabs/react";
import { Loader2, Mic, Square } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  fetchVoiceSignedUrl,
  getPublicAgentId,
  submitVoiceIntake,
  type VoiceIntakeResult,
} from "@/lib/voice";

type Props = {
  disabled?: boolean;
  profileUserId?: string;
  onIntakeComplete: (payload: VoiceIntakeResult) => void;
  onError?: (message: string) => void;
};

function VoiceWave({ active }: { active: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { getInputByteFrequencyData, getOutputByteFrequencyData } = useConversationControls();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let frame = 0;
    const draw = () => {
      frame = requestAnimationFrame(draw);
      const w = canvas.width;
      const h = canvas.height;
      if (w <= 0 || h <= 0 || !Number.isFinite(w) || !Number.isFinite(h)) return;

      ctx.clearRect(0, 0, w, h);

      if (!active) {
        ctx.fillStyle = "rgba(76, 175, 80, 0.15)";
        for (let i = 0; i < 24; i++) {
          const barH = 4 + Math.sin(frame * 0.02 + i * 0.4) * 3;
          ctx.fillRect(8 + i * 14, h / 2 - barH / 2, 8, barH);
        }
        return;
      }

      const output = getOutputByteFrequencyData();
      const input = getInputByteFrequencyData();
      const data = output?.length ? output : input;
      const dataLen = data?.length ?? 0;
      const bars = 24;
      for (let i = 0; i < bars; i++) {
        const idx =
          dataLen > 0 ? Math.min(dataLen - 1, Math.floor((i / bars) * dataLen)) : 0;
        const sample = dataLen > 0 ? Number(data![idx]) : 0;
        const v = Number.isFinite(sample) ? Math.min(1, Math.max(0, sample / 255)) : 0;
        const barH = Math.min(h - 1, Math.max(4, v * h * 0.85));
        const yTop = h - barH;
        const gradient = ctx.createLinearGradient(0, yTop, 0, h);
        gradient.addColorStop(0, "#4CAF50");
        gradient.addColorStop(1, "#2E7D32");
        ctx.fillStyle = gradient;
        ctx.fillRect(8 + i * 14, Math.max(0, yTop - 4), 8, barH);
      }
    };

    draw();
    return () => cancelAnimationFrame(frame);
  }, [active, getInputByteFrequencyData, getOutputByteFrequencyData]);

  return (
    <canvas
      ref={canvasRef}
      width={360}
      height={72}
      className="w-full max-w-sm rounded-xl bg-[#1b3d1f]/10"
      aria-hidden
    />
  );
}

function VoiceConsoleInner({
  disabled,
  profileUserId,
  onIntakeComplete,
  onError,
}: Props) {
  const { status } = useConversationStatus();
  const { startSession, endSession } = useConversationControls();
  const [transcriptParts, setTranscriptParts] = useState<string[]>([]);
  const [processing, setProcessing] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  useConversation({
    onMessage: (message) => {
      const text =
        typeof message === "object" && message !== null && "message" in message
          ? String((message as { message?: string }).message ?? "")
          : typeof message === "string"
            ? message
            : "";
      if (!text.trim()) return;
      const source =
        typeof message === "object" && message !== null && "source" in message
          ? String((message as { source?: string }).source ?? "")
          : "";
      if (source === "user" || source === "microphone") {
        setTranscriptParts((prev) => [...prev, text.trim()]);
      }
    },
    onError: (error: unknown) => {
      const msg =
        error instanceof Error ? error.message : String(error ?? "Voice session error.");
      setLocalError(msg);
      onError?.(msg);
    },
    overrides: {
      agent: {
        firstMessage:
          "Vanakkam! I'm Agri-Lend. You can speak in Tamil or English. Tell me your crop, how many acres you farm, and how much you need in Sri Lankan rupees.",
        ...(process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_LANGUAGE
          ? { language: process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_LANGUAGE }
          : {}),
      },
    },
  });

  const connected = status === "connected";
  const connecting = status === "connecting";

  const startVoice = useCallback(async () => {
    if (disabled || connecting || connected) return;
    setLocalError(null);
    setTranscriptParts([]);

    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      const msg = "Microphone access is required for voice apply.";
      setLocalError(msg);
      onError?.(msg);
      return;
    }

    try {
      const agentId = getPublicAgentId();
      if (agentId) {
        await startSession({ agentId });
        return;
      }
      const signedUrl = await fetchVoiceSignedUrl();
      await startSession({ signedUrl });
    } catch (e) {
      const msg =
        e instanceof Error
          ? e.message
          : "Could not start voice session. Configure ELEVENLABS_AGENT_ID.";
      setLocalError(msg);
      onError?.(msg);
    }
  }, [connected, connecting, disabled, onError, startSession]);

  const stopVoice = useCallback(async () => {
    if (!connected) return;
    await endSession();
  }, [connected, endSession]);

  const applyVoiceIntake = useCallback(async () => {
    const transcript = transcriptParts.join("\n").trim();
    if (transcript.length < 8) {
      const msg = "Speak about your crop, acreage, and loan amount first.";
      setLocalError(msg);
      onError?.(msg);
      return;
    }

    setProcessing(true);
    setLocalError(null);
    try {
      if (connected) await endSession();
      const result = await submitVoiceIntake(transcript, profileUserId);
      onIntakeComplete(result);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Voice intake failed.";
      setLocalError(msg);
      onError?.(msg);
    } finally {
      setProcessing(false);
    }
  }, [
    connected,
    endSession,
    onError,
    onIntakeComplete,
    profileUserId,
    transcriptParts,
  ]);

  return (
    <div className="flex flex-col items-center gap-4">
      <VoiceWave active={connected || connecting} />

      <div className="flex flex-wrap items-center justify-center gap-3">
        {!connected ? (
          <button
            type="button"
            disabled={disabled || connecting || processing}
            onClick={() => void startVoice()}
            className="flex h-20 w-20 items-center justify-center rounded-full bg-[#4CAF50] text-white shadow-lg shadow-green-200 transition-transform hover:scale-105 active:scale-95 disabled:opacity-50"
            aria-label="Start voice conversation"
          >
            {connecting ? (
              <Loader2 className="h-9 w-9 animate-spin" />
            ) : (
              <Mic className="h-9 w-9" />
            )}
          </button>
        ) : (
          <button
            type="button"
            disabled={processing}
            onClick={() => void stopVoice()}
            className="flex h-16 w-16 items-center justify-center rounded-full border-2 border-[#2E7D32] bg-white text-[#2E7D32] shadow-md"
            aria-label="Stop voice conversation"
          >
            <Square className="h-6 w-6 fill-current" />
          </button>
        )}

        <button
          type="button"
          disabled={disabled || processing || transcriptParts.length === 0}
          onClick={() => void applyVoiceIntake()}
          className="rounded-full bg-[#2E7D32] px-5 py-2.5 text-sm font-medium text-white hover:bg-[#1b5e20] disabled:opacity-50"
        >
          {processing ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Processing…
            </span>
          ) : (
            "Apply voice details"
          )}
        </button>
      </div>

      <div className="text-center">
        <p className="font-semibold text-[#2E7D32]">
          {connected ? "Listening…" : "Speak to apply"}
        </p>
        <p className="mt-1 text-xs text-gray-500">
          {connected
            ? "Describe crop, acreage, and loan amount — then tap Apply voice details."
            : "Voice: Tamil or English (ElevenLabs). Sinhala: use the form fields below."}
        </p>
      </div>

      {transcriptParts.length > 0 && (
        <div className="w-full max-w-md rounded-lg border border-gray-100 bg-white/80 p-3 text-left text-xs text-gray-600">
          <p className="mb-1 font-medium text-gray-800">Captured speech</p>
          <p className="line-clamp-4 whitespace-pre-wrap">{transcriptParts.join(" ")}</p>
        </div>
      )}

      {localError && (
        <p className="max-w-md text-center text-sm text-red-600">{localError}</p>
      )}
    </div>
  );
}

export function RealtimeVoiceConsole(props: Props) {
  return (
    <ConversationProvider>
      <VoiceConsoleInner {...props} />
    </ConversationProvider>
  );
}
