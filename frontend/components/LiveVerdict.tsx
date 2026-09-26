"use client";

import { useEffect, useRef, useState } from "react";
import { GradeBadge } from "@/components/GradeBadge";
import { judgePrompt } from "@/lib/api";
import type { ChatMessage, JudgeResult, Mode, Verdict } from "@/lib/types";

const LABEL: Record<Verdict, string> = {
  efficient: "Efficient",
  okay: "Okay",
  wasteful: "Wasteful",
  horrible: "Horrible",
};

// The judge's fast mode (rules only), called while the player types. It never
// shows the round's answer key: missing details come back as short hints.
// In collaborate mode each partner's piece counts too, so the mode is sent.
export function LiveVerdict({
  prompt,
  challengeId,
  mode,
  turn,
  history,
}: {
  prompt: string;
  challengeId: string | undefined;
  mode: Mode;
  turn: number;
  history: ChatMessage[];
}) {
  const [result, setResult] = useState<JudgeResult | null>(null);
  const [checking, setChecking] = useState(false);
  const historyRef = useRef(history);
  historyRef.current = history;
  const historyKey = history.length;

  useEffect(() => {
    const text = prompt.trim();
    if (!text) {
      setResult(null);
      setChecking(false);
      return;
    }
    const controller = new AbortController();
    setChecking(true);
    const timer = window.setTimeout(() => {
      judgePrompt(
        { prompt: text, mode: "fast", context: { challengeId, turn, history: historyRef.current, gameMode: mode } },
        controller.signal,
      )
        .then((data) => {
          if (!controller.signal.aborted) setResult(data);
        })
        .catch(() => undefined)
        .finally(() => {
          if (!controller.signal.aborted) setChecking(false);
        });
    }, 400);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [prompt, challengeId, mode, turn, historyKey]);

  if (!prompt.trim()) {
    return <p className="live-verdict is-empty">The judge checks your message as you type, before you send it.</p>;
  }
  if (!result) {
    return <p className="live-verdict is-empty">Checking your message…</p>;
  }

  const secret = result.reasons.find((line) => line.tone === "bad");
  return (
    <div className={`live-verdict is-${result.verdict}${checking ? " is-checking" : ""}`} aria-live="polite">
      <div className="live-verdict__head">
        <GradeBadge grade={result.grade} />
        <strong>{LABEL[result.verdict]}</strong>
        <span className="live-verdict__tokens">
          {result.tokens.effective.toLocaleString()} tokens · budget {result.tokens.budget}
        </span>
      </div>
      {secret ? <p className="live-verdict__bad">{secret.text}</p> : null}
      {result.missing.length ? (
        <p>
          Missing: {result.missing.join(", ")}. Each one is a web lookup (+1,200).
        </p>
      ) : (
        <p>Has the key details. The model can answer without looking anything up.</p>
      )}
      {result.tokens.ask ? <p>Say what you want: fix, change, why, how… (+{result.tokens.ask})</p> : null}
      {result.tokens.output ? <p>Asks for more output than it needs (+{result.tokens.output})</p> : null}
      {result.flags.slice(0, 2).map((flag) => (
        <p key={flag} className="muted small">
          {flag}
        </p>
      ))}
    </div>
  );
}
