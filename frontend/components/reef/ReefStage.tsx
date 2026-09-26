"use client";

import { QRCodeSVG } from "qrcode.react";
import { GradeBadge } from "@/components/GradeBadge";
import { Leaderboard } from "@/components/Leaderboard";
import { AmbientLife, BandArt, Bloom, Fish, SludgeBarrel, Turtle } from "@/components/reef/FallbackReef";
import { reefLabel, slot } from "@/lib/reef";
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
  const residents = session.events
    .filter((event) => event.type === "turtle" || event.type === "bloom" || event.type === "fish")
    .slice(0, 8);
  const shock = liveEvent?.type === "sludge" || liveEvent?.type === "murk";

  return (
    <section className={`reef reef--${band}`} style={{ ["--health" as string]: health }}>
      <BandArt band={band} />
      <AmbientLife />
      <div className="reef__murk" />
      {shock && liveEvent ? <div key={liveEvent.id} className="reef__flash" /> : null}
      {liveEvent?.type === "sludge" ? <SludgeBarrel key={liveEvent.id} /> : null}

      <div className="reef__residents" aria-hidden>
        {residents.map((event) => (
          <figure key={event.id} className="resident" style={{ left: `${slot(event.id)}%`, bottom: `${12 + (slot(event.id) % 18)}%` }}>
            <Reward event={event} />
            <figcaption>{event.actor}</figcaption>
          </figure>
        ))}
      </div>

      {liveEvent && (liveEvent.type === "turtle" || liveEvent.type === "bloom") ? (
        <div key={liveEvent.id} className="reef__toast">
          <Reward event={liveEvent} />
          <div>
            <strong>{liveEvent.title}</strong>
            <p>{liveEvent.grade} · the reef recovers a little</p>
          </div>
        </div>
      ) : null}

      <header className="reef__hud">
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

// The judge's numbers for the most recent turn, big enough to read from the table.
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
  if (event.type === "turtle") return <Turtle />;
  if (event.type === "bloom") return <Bloom />;
  return <Fish />;
}
