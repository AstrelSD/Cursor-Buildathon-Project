"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

type ToastType = "success" | "error";

type ToastItem = {
  id: string;
  message: string;
  type: ToastType;
};

type ToastOptions = {
  message: string;
  type?: ToastType;
  durationMs?: number;
};

type ToastContextValue = {
  toast: (options: ToastOptions) => void;
  success: (message: string) => void;
  error: (message: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const TOAST_STYLES: Record<ToastType, string> = {
  success:
    "border-[#2E7D32]/30 bg-white text-[#1b5e20] shadow-lg shadow-green-100/80",
  error: "border-red-200 bg-white text-red-800 shadow-lg shadow-red-100/80",
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((current) => current.filter((item) => item.id !== id));
  }, []);

  const toast = useCallback(
    ({ message, type = "success", durationMs = 4500 }: ToastOptions) => {
      const id =
        typeof crypto !== "undefined" && crypto.randomUUID
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random()}`;

      setToasts((current) => [...current, { id, message, type }]);

      window.setTimeout(() => dismiss(id), durationMs);
    },
    [dismiss],
  );

  const value = useMemo<ToastContextValue>(
    () => ({
      toast,
      success: (message: string) => toast({ message, type: "success" }),
      error: (message: string) => toast({ message, type: "error" }),
    }),
    [toast],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        className="pointer-events-none fixed top-4 right-4 z-[100] flex w-full max-w-sm flex-col gap-2 px-4 sm:px-0"
        aria-live="polite"
        aria-atomic="true"
      >
        {toasts.map((item) => (
          <div
            key={item.id}
            role="status"
            className={`pointer-events-auto rounded-lg border px-4 py-3 text-sm font-medium ${TOAST_STYLES[item.type]}`}
          >
            {item.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
