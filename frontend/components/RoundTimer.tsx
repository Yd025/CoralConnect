"use client";

import { useEffect, useState } from "react";

export const ROUND_MS = 120_000;

export function useRoundRemaining(startedAt: number, active: boolean): number | null {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!startedAt || !active) return;
    const timer = window.setInterval(() => setNow(Date.now()), 250);
    return () => window.clearInterval(timer);
  }, [startedAt, active]);
  if (!startedAt || !active) return null;
  return Math.max(0, Math.ceil((startedAt * 1000 + ROUND_MS - now) / 1000));
}

export function formatClock(seconds: number): string {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

export function RoundTimer({ startedAt, active }: { startedAt: number; active: boolean }) {
  const remaining = useRoundRemaining(startedAt, active);
  if (remaining == null) return null;
  return (
    <p className="round-timer" role="timer" aria-live="polite">
      {formatClock(remaining)}
    </p>
  );
}
