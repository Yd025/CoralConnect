"use client";

import { QRCodeSVG } from "qrcode.react";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { GradeBadge } from "@/components/GradeBadge";
import { createSession } from "@/lib/api";
import { playUrl, useBoothOrigin } from "@/lib/booth";
import { personLine } from "@/lib/connection";
import type { Grade } from "@/lib/types";
import { useSession } from "@/lib/useSession";

const ADMIN_KEY = "coral-admin";

export default function CompeteBoardPage() {
  const router = useRouter();
  const params = useParams<{ code: string }>();
  const code = String(params.code || "").toUpperCase();
  const { session, error, connected } = useSession(code);
  const { origin } = useBoothOrigin();
  const [busy, setBusy] = useState(false);
  const play = origin ? playUrl(origin, code) : "";
  const roster = (session?.players ?? []).filter((player) => player.id !== "p_rehearsal");
  const top = [...roster].sort((a, b) => b.score - a.score || a.name.localeCompare(b.name)).slice(0, 3);
  const ended = session?.status === "ended";

  async function newCompetition() {
    setBusy(true);
    try {
      const created = await createSession("compete", session?.challenge?.id || "farm-water");
      window.localStorage.setItem(
        ADMIN_KEY,
        JSON.stringify({ code: created.session.code, adminToken: created.adminToken }),
      );
      router.push("/admin");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="phone board-page">
      <div className="topbar">
        <a className="brand" href="/admin">CoralConnect</a>
        <span className={connected ? "pill is-live" : "pill"}>{connected ? "Live" : "Connecting"}</span>
      </div>
      <p className="eyebrow">Competition {code}</p>
      {!session ? <h1>{error || "Looking for this competition…"}</h1> : null}
      {session && !ended ? (
        <section className="panel stack">
          <h1>{session.challenge?.title || "Competition"}</h1>
          <p>{roster.length} of {session.playerMax} players. {session.status === "lobby" ? "Waiting to start." : "Round in progress."}</p>
          <p className="muted">This screen switches to the top 3 when the round ends.</p>
          {play ? (
            <div className="qr-card">
              <QRCodeSVG value={play} size={168} bgColor="#f4fff9" fgColor="#042630" />
              <p>Scan to join</p>
            </div>
          ) : null}
          <p className="link-line">{play}</p>
          <ol className="roster">
            {roster.map((player) => (
              <li key={player.id}>
                <span>
                  <strong>{player.name}</strong>
                  <small>{personLine(player.builds, player.cares)}</small>
                </span>
                <b>{player.score}</b>
              </li>
            ))}
          </ol>
        </section>
      ) : null}
      {session && ended ? (
        <section className="panel stack">
          <h1>Top 3 prompters</h1>
          <p className="muted">Higher means the prompt judge found less wasted work.</p>
          {top.length === 0 ? <p>Nobody finished this round.</p> : null}
          <ol className="podium">
            {top.map((player, index) => (
              <li key={player.id}>
                <span className="board__rank">{index + 1}</span>
                <span>
                  <strong>{player.name}</strong>
                  <small>{personLine(player.builds, player.cares)}</small>
                </span>
                <GradeBadge grade={player.lastGrade as Grade | null} />
                <b>{player.score}</b>
              </li>
            ))}
          </ol>
          <button className="btn" type="button" disabled={busy} onClick={() => void newCompetition()}>
            {busy ? "Opening…" : "New competition"}
          </button>
        </section>
      ) : null}
    </main>
  );
}
