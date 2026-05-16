"use client";

import { ImagePlus, Loader2, X } from "lucide-react";
import { useId, useRef } from "react";

const ACCEPT = "image/jpeg,image/png,image/webp";
const MAX_BYTES = 10 * 1024 * 1024;

type Props = {
  file: File | null;
  previewUrl: string | null;
  disabled?: boolean;
  onFileSelect: (file: File | null) => void;
  onValidationError?: (message: string) => void;
  error?: string | null;
};

export function MultimodalUploader({
  file,
  previewUrl,
  disabled = false,
  onFileSelect,
  onValidationError,
  error,
}: Props) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);

  function handleChange(list: FileList | null) {
    const selected = list?.[0];
    if (!selected) return;

    if (!selected.type.startsWith("image/")) {
      onValidationError?.("Please choose a JPEG, PNG, or WebP image.");
      onFileSelect(null);
      return;
    }
    if (selected.size > MAX_BYTES) {
      onValidationError?.("Image must be 10 MB or smaller.");
      onFileSelect(null);
      return;
    }
    onFileSelect(selected);
  }

  function clear() {
    onFileSelect(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div>
      <input
        ref={inputRef}
        id={inputId}
        type="file"
        accept={ACCEPT}
        className="sr-only"
        disabled={disabled}
        onChange={(e) => handleChange(e.target.files)}
      />

      {previewUrl ? (
        <div className="relative overflow-hidden rounded-xl border border-gray-200">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={previewUrl}
            alt="Farm evidence preview"
            className="max-h-56 w-full object-cover"
          />
          {!disabled && (
            <button
              type="button"
              onClick={clear}
              className="absolute right-2 top-2 rounded-full bg-black/50 p-1.5 text-white hover:bg-black/70"
              aria-label="Remove photo"
            >
              <X className="h-4 w-4" />
            </button>
          )}
          {file && (
            <p className="border-t border-gray-100 bg-white px-3 py-2 text-xs text-gray-500">
              {file.name} ({(file.size / 1024).toFixed(0)} KB)
            </p>
          )}
        </div>
      ) : (
        <label
          htmlFor={inputId}
          className={`flex min-h-[160px] w-full cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-6 text-center transition-colors ${
            disabled
              ? "cursor-not-allowed border-gray-200 bg-gray-50 opacity-60"
              : "border-gray-300 bg-gray-50/50 hover:border-[#4CAF50] hover:bg-green-50/30"
          }`}
        >
          {disabled ? (
            <Loader2 className="h-10 w-10 animate-spin text-gray-400" />
          ) : (
            <ImagePlus className="h-10 w-10 text-gray-400" />
          )}
          <p className="mt-3 font-medium text-gray-700">
            {disabled ? "Uploading…" : "Tap here to add a field photo"}
          </p>
          <p className="mt-1 text-sm text-gray-500">
            JPEG, PNG or WebP · max 10 MB
          </p>
        </label>
      )}

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
