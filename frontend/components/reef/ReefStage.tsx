"use client";

import { QRCodeSVG } from "qrcode.react";
import { Leaderboard } from "@/components/Leaderboard";
import { AmbientLife, BandArt, SludgeBarrel } from "@/components/reef/FallbackReef";
import { reefLabel } from "@/lib/reef";
import type { GameSession, ReefEvent } from "@/lib/types";

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
                <span>{latest.actor}</span>
                {clip(latest.prompt)}
              </p>
              <p className="reef__ai-reply">{clip(latest.aiResponse)}</p>
            </>
          ) : (
            <p className="reef__ai-reply">Waiting for a message. Prompt Grok from a phone.</p>
          )}
        </div>
      </aside>

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
        <p className="reef__latest">{session.events[0]?.title}</p>
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

function Reward({ event }: { event: ReefEvent }) {
  if (event.imageUrl) {
    return <img className="reward-img" src={event.imageUrl} alt="" />;
  }
  return <img className="reward-img reward-svg" src={REWARD_ART[event.type] ?? REWARD_ART.fish} alt="" />;
}
