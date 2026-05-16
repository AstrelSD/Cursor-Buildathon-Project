"use client";

import { useEffect, useRef, useState } from "react";

import { logsFromLoanTransition, seedLog, type TerminalLogEntry } from "@/lib/loan-logs";
import { getSupabase, type LoanRow } from "@/lib/supabase";

const MAX_LINES = 200;

type Props = {
  className?: string;
  initialLoans?: LoanRow[];
};

export function UnderwritingTerminal({ className = "", initialLoans = [] }: Props) {
  const [logs, setLogs] = useState<TerminalLogEntry[]>([seedLog()]);
  const loanSnapshot = useRef<Map<string, LoanRow>>(new Map());
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    for (const loan of initialLoans) {
      loanSnapshot.current.set(loan.id, loan);
    }
  }, [initialLoans]);

  useEffect(() => {
    const supabase = getSupabase();

    const channel = supabase
      .channel("loans-underwriting-terminal")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "loans" },
        (payload) => {
          const row = payload.new as LoanRow | undefined;
          if (!row?.id) return;

          const previous = loanSnapshot.current.get(row.id) ?? null;
          loanSnapshot.current.set(row.id, row);

          const entries = logsFromLoanTransition(previous, row);
          if (entries.length === 0) return;

          setLogs((prev) => [...prev, ...entries].slice(-MAX_LINES));
        },
      )
      .subscribe();

    return () => {
      void supabase.removeChannel(channel);
    };
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [logs]);

  return (
    <section
      className={`flex flex-col overflow-hidden rounded-2xl border border-emerald-500/20 bg-black/60 shadow-[0_0_40px_rgba(16,185,129,0.08)] backdrop-blur-xl ${className}`}
    >
      <header className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <TerminalDots />
        <span className="font-mono text-xs uppercase tracking-widest text-emerald-400/90">
          Underwriting Terminal
        </span>
        <span className="animate-pulse font-mono text-[10px] text-emerald-500">LIVE</span>
      </header>
      <div
        ref={scrollRef}
        className="h-72 flex-1 overflow-y-auto px-4 py-3 font-mono text-xs leading-relaxed"
      >
        {logs.map((line) => (
          <div key={line.id} className={`mb-1 ${levelClass(line.level)}`}>
            <span className="text-zinc-600">{line.at}</span> {line.message}
          </div>
        ))}
      </div>
    </section>
  );
}

function TerminalDots() {
  return (
    <div className="flex gap-1.5">
      <span className="h-2.5 w-2.5 rounded-full bg-rose-500/80" />
      <span className="h-2.5 w-2.5 rounded-full bg-amber-400/80" />
      <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/80" />
    </div>
  );
}

function levelClass(level: TerminalLogEntry["level"]): string {
  switch (level) {
    case "success":
      return "text-emerald-400";
    case "warn":
      return "text-amber-400";
    case "error":
      return "text-rose-400";
    default:
      return "text-zinc-300";
  }
}
