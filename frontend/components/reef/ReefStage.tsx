"use client";

import { useEffect, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { GradeBadge } from "@/components/GradeBadge";
import { Leaderboard } from "@/components/Leaderboard";
import { RoundTimer } from "@/components/RoundTimer";
import { AmbientLife, BandArt, SludgeBarrel } from "@/components/reef/FallbackReef";
import { reefLabel } from "@/lib/reef";
import type { GameSession, ReefEvent, Submission } from "@/lib/types";

export function ReefStage({
  session,
  liveEvent,
  playLink,
}: {
  session: GameSession;
  liveEvent: ReefEvent | null;
  playLink: string;
}) {
  const health = session.reefHealth;
  const band = session.reefBand;
  const shock = liveEvent?.type === "sludge" || liveEvent?.type === "murk";
  const latest = session.submissions[0] ?? null;
  const showClock = session.mode === "compete" && session.status === "playing" && session.startedAt > 0;
  const [open, setOpen] = useState(false);
  useEffect(() => {
    setOpen(false);
  }, [latest?.id]);

  return (
    <section className={`reef reef--${band}`} style={{ ["--health" as string]: health }}>
      <BandArt band={band} />
      <AmbientLife band={band} health={health} />
      <div className="reef__murk" />
      {shock && liveEvent ? <div key={liveEvent.id} className="reef__flash" /> : null}
      {liveEvent?.type === "sludge" ? <SludgeBarrel key={liveEvent.id} seed={liveEvent.id} /> : null}

      {liveEvent && (liveEvent.type === "turtle" || liveEvent.type === "bloom") ? (
        <div key={liveEvent.id} className="reef__toast">
          <Reward event={liveEvent} />
          <div>
            <strong>{liveEvent.title}</strong>
            <p>{liveEvent.grade} · the reef recovers a little</p>
          </div>
        </div>
      ) : null}

      <aside className="reef__ai">
        <img src="/reef/05-otto-octopus.svg" alt="" />
        <div>
          <p className="eyebrow">Prompt</p>
          <strong>Grok</strong>
          {latest ? (
            <>
              <p className="reef__ai-prompt">
                <span>{latest.actor} · {latest.grade}</span>
                {latest.reasonable
                  ? "The source was in the message."
                  : "The source was missing, so Grok searched."}
              </p>
              <button className="btn-ghost" type="button" onClick={() => setOpen((value) => !value)}>
                {open ? "Hide the details" : latest.reasonable ? "See Grok's answer" : "See the problems"}
              </button>
              {open ? (
                <div className="reef__ai-details">
                  <p>{latest.verdictReason || latest.summary}</p>
                  <p>{clip(latest.aiResponse, 360)}</p>
                </div>
              ) : null}
            </>
          ) : (
            <p className="reef__ai-reply">Waiting for a message. Prompt Grok from a phone.</p>
          )}
        </div>
      </aside>

      {showClock ? <RoundTimer startedAt={session.startedAt} active /> : null}
      <header className={showClock ? "reef__hud has-clock" : "reef__hud"}>
        <div>
          <p className="eyebrow">CoralConnect · {session.mode === "collaborate" ? "Pairs start on their own" : "One round · up to 10"}</p>
          <h1>{session.challenge?.title}</h1>
        </div>
        <div className="health">
          <span>{reefLabel(band)}</span>
          <strong>{health}</strong>
          <i>
            <b style={{ width: `${health}%` }} />
          </i>
        </div>
      </header>

      <div className="reef__side">
        <Leaderboard session={session} compact />
      </div>

      <footer className="reef__foot">
        {playLink ? (
          <div className="reef__qr">
            <QRCodeSVG value={playLink} size={112} bgColor="#f4fff9" fgColor="#042630" />
            <div>
              <strong>Scan to play</strong>
              <p>{session.code}</p>
            </div>
          </div>
        ) : null}
        <div className="reef__footnote">
          <LastTurn submission={session.submissions[0]} />
          <p className="reef__latest">{session.events[0]?.title}</p>
        </div>
      </footer>
    </section>
  );
}

const REWARD_ART: Record<string, string> = {
  turtle: "/reef/02-moss-turtle.svg",
  bloom: "/reef/10-coral-bloom.svg",
  fish: "/reef/04-pip-fish.svg",
};

function clip(text: string, max = 220) {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= max) return clean;
  return `${clean.slice(0, max).trim()}…`;
}

function LastTurn({ submission }: { submission: Submission | undefined }) {
  if (!submission) return null;
  const verdict = submission.verdict || (submission.reasonable ? "okay" : "wasteful");
  return (
    <div className="reef__turn">
      <div className="reef__turn-head">
        <GradeBadge grade={submission.grade} />
        <strong>{submission.actor}</strong>
        <span className="reef__turn-verdict">{verdict}</span>
      </div>
      <p>
        {(submission.effectiveTokens || submission.tokenCount).toLocaleString()} tokens of model work
        {submission.savedVsVague > 0 ? ` · saved ${submission.savedVsVague.toLocaleString()} vs a vague prompt` : ""}
      </p>
      {submission.measuredTokens > 0 ? (
        <p>
          Real Grok run: {submission.measuredTokens.toLocaleString()} tokens
          {submission.betterMeasuredTokens > 0
            ? ` · better prompt ${submission.betterMeasuredTokens.toLocaleString()} · saved ${submission.measuredSaved.toLocaleString()}`
            : ""}
        </p>
      ) : null}
    </div>
  );
}

function Reward({ event }: { event: ReefEvent }) {
  if (event.imageUrl) {
    return <img className="reward-img" src={event.imageUrl} alt="" />;
  }
  return <img className="reward-img reward-svg" src={REWARD_ART[event.type] ?? REWARD_ART.fish} alt="" />;
}
