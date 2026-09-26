"use client";

import { QRCodeSVG } from "qrcode.react";
import { FormEvent, useEffect, useState } from "react";
import { AnimatedBackground } from "@/components/AnimatedBackground";
import { Leaderboard } from "@/components/Leaderboard";
import { apiBase, createSession, endSession, getChallenges, getHealth, setChallenge, simulate, startSession } from "@/lib/api";
import { playUrl, stageUrl, useBoothOrigin } from "@/lib/booth";
import { reefLabel } from "@/lib/reef";
import type { Challenge, Health, Mode } from "@/lib/types";
import { useSession } from "@/lib/useSession";

const ADMIN_KEY = "coral-admin";

type SavedAdmin = { code: string; adminToken: string };

export default function AdminPage() {
  const { origin, host, updateHost } = useBoothOrigin();
  const [health, setHealth] = useState<Health | null>(null);
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [mode, setMode] = useState<Mode>("collaborate");
  const [challengeId, setChallengeId] = useState("invoice-bug");
  const [saved, setSaved] = useState<SavedAdmin | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState("");
  const { session, connected } = useSession(saved?.code ?? null);

  useEffect(() => {
    const raw = window.localStorage.getItem(ADMIN_KEY);
    if (raw) {
      try {
        setSaved(JSON.parse(raw) as SavedAdmin);
      } catch {
        window.localStorage.removeItem(ADMIN_KEY);
      }
    }
    getHealth().then(setHealth).catch((err: Error) => setError(err.message));
    getChallenges()
      .then((data) => setChallenges((data.challenges ?? []).filter((item): item is Challenge => Boolean(item))))
      .catch(() => undefined);
  }, []);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const created = await createSession(mode, challengeId);
      const next = { code: created.session.code, adminToken: created.adminToken };
      window.localStorage.setItem(ADMIN_KEY, JSON.stringify(next));
      setSaved(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the game.");
    } finally {
      setBusy(false);
    }
  }

  async function run(action: () => Promise<unknown>) {
    if (!saved) return;
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : "That did not work.");
    } finally {
      setBusy(false);
    }
  }

  async function copy(value: string, label: string) {
    await navigator.clipboard.writeText(value);
    setCopied(label);
  }

  const play = saved && origin ? playUrl(origin, saved.code) : "";
  const stage = saved && origin ? stageUrl(origin, saved.code) : "";

  return (
    <main className="landing admin-page">
      <AnimatedBackground />
      <div className="shell landing-ui">
        <header className="landing-top">
          <a className="brand" href="/">
            <svg className="brand-mark" viewBox="0 0 28 28" aria-hidden="true">
              <path d="M14 3 L16.2 11.2 L14 9.4 L11.8 11.2 Z" fill="currentColor" />
              <path d="M6 8 L9.2 13.2 L8 12 L6.6 14.2 Z" fill="currentColor" />
              <path d="M22 8 L18.8 13.2 L20 12 L21.4 14.2 Z" fill="currentColor" />
              <path d="M14 10.5 V24" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
            </svg>
            CoralConnect
          </a>
          <nav className="landing-nav" aria-label="Site">
            <a href="/">The reef</a>
          </nav>
          <div className="landing-tools">
            <span>HackGT booth</span>
            <span className={connected ? "pill is-live" : "pill"}>{connected ? "Live" : "Connecting"}</span>
          </div>
        </header>

        <div className="admin-layout">
          <section className="admin-intro" aria-labelledby="admin-title">
            <p className="hero-kicker"><i />Booth console</p>
            <h1 id="admin-title">Set the game.</h1>
            <p className="lede">Then point people at the reef. This laptop keeps the code, the QR, and the shared water.</p>
            {error ? <p className="error">{error}</p> : null}
            <p className="muted">
              Engine: {apiBase()}
              {health ? ` · ${health.grokConfigured ? `Grok live (${health.chatModel})` : "Grok key not set — grades still run, answers are simulated"}` : ""}
            </p>
            <form className="panel stack" onSubmit={onCreate}>
          <div className="mode-grid">
            <button type="button" className={mode === "collaborate" ? "mode is-on" : "mode"} onClick={() => setMode("collaborate")}>
              <strong>Collaborate</strong>
              <small>Pair strangers by language into a reef squad. They share one prompt and one score.</small>
            </button>
            <button type="button" className={mode === "compete" ? "mode is-on" : "mode"} onClick={() => setMode("compete")}>
              <strong>Compete</strong>
              <small>Everyone writes alone. Less extra model work ranks higher. The reef is still shared.</small>
            </button>
          </div>
          <label>
            Challenge
            <select value={challengeId} onChange={(event) => setChallengeId(event.target.value)}>
              {(challenges.length ? challenges : [{ id: "invoice-bug", title: "Invoice bug", brief: "", hint: "", turnCount: 2, targetTokens: 200, beats: [] }]).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.title} · {item.turnCount || item.beats.length || 2} turns
                </option>
              ))}
            </select>
          </label>
          <button className="btn" disabled={busy} type="submit">
            {saved ? "Start a fresh game" : "Create game and QR"}
          </button>
          <p className="muted">The admin key stays in this browser. Keep the tab open during the demo.</p>
            </form>
          </section>

          <section className="panel stack admin-side">
          {!saved || !session ? (
            <p className="muted">The QR code shows up here. Phones should be on the same Wi-Fi as this laptop.</p>
          ) : (
            <>
              <div className="code-block">
                <div>
                  <p className="eyebrow">{session.mode} · {session.status}</p>
                  <strong>{session.code}</strong>
                </div>
                {play ? (
                  <div className="qr-card">
                    <QRCodeSVG value={play} size={168} bgColor="#f4fff9" fgColor="#042630" />
                    <p>Scan to join</p>
                  </div>
                ) : null}
              </div>
              <label>
                Phone link host
                <input value={host} onChange={(event) => updateHost(event.target.value)} />
              </label>
              <p className="link-line">{play}</p>
              <div className="btn-row">
                <button className="btn-ghost" type="button" onClick={() => copy(play, "play")}>
                  {copied === "play" ? "Copied" : "Copy join link"}
                </button>
                <button className="btn" type="button" onClick={() => window.open(stage, "coral-stage")}>
                  Open main stage
                </button>
              </div>
              <div className="health-inline">
                <span>{reefLabel(session.reefBand)} · reef {session.reefHealth}</span>
                <i><b style={{ width: `${session.reefHealth}%` }} /></i>
              </div>
              <div className="btn-row">
                <button className="btn" type="button" disabled={busy || session.status === "playing"} onClick={() => run(() => startSession(saved.code, saved.adminToken))}>
                  Start round
                </button>
                <button className="btn-ghost" type="button" disabled={busy || session.status !== "playing"} onClick={() => run(() => setChallenge(saved.code, saved.adminToken, challengeId))}>
                  Apply challenge
                </button>
                <button className="btn-danger" type="button" disabled={busy || session.status === "ended"} onClick={() => run(() => endSession(saved.code, saved.adminToken))}>
                  End game
                </button>
              </div>
              <h2>Players</h2>
              {session.players.filter((player) => player.id !== "p_rehearsal").length === 0 ? (
                <p className="muted">Nobody has scanned in yet.</p>
              ) : (
                <ul className="roster">
                  {session.players.filter((player) => player.id !== "p_rehearsal").map((player) => (
                    <li key={player.id}>
                      <span>
                        <strong>{player.name}</strong>
                        <small>{player.language}{player.connected ? "" : " · left"}</small>
                      </span>
                      <b>{player.score}</b>
                    </li>
                  ))}
                </ul>
              )}
              <details>
                <summary>Booth rehearsal</summary>
                <p className="muted">Drops a fake prompt into this game so you can check the reef before anyone arrives. It adds a Rehearsal player.</p>
                <div className="btn-row">
                  <button className="btn-ghost" type="button" disabled={busy} onClick={() => run(() => simulate(saved.code, saved.adminToken, "efficient"))}>
                    Adequate prompt
                  </button>
                  <button className="btn-ghost" type="button" disabled={busy} onClick={() => run(() => simulate(saved.code, saved.adminToken, "bloated"))}>
                    Vague prompt
                  </button>
                </div>
              </details>
            </>
          )}
          </section>
        </div>

        {session ? (
          <div className="panel admin-board">
            <Leaderboard session={session} />
          </div>
        ) : null}

        <details className="panel admin-pitch">
        <summary>60 second pitch</summary>
        <p>
          A thin prompt that leaves out the source makes the model look the fact up. That extra work is the waste.
          People at the table get paired into reef squads, or they compete, and each round takes two messages so one prompt is not enough.
          Include the source and the reef holds. Leave it out and the lookup drops sludge in the water.
        </p>
        {health ? (
          <p className="muted">
            Carbon model: {health.formula.energyKwhPer1kTokens} kWh per 1,000 lookup tokens × {health.formula.carbonGramsPerKwh} g CO2/kWh.
            A missing source is charged as {health.formula.webLookupTokens} lookup tokens.
            Waste is also shown as if a million developers sent that thin prompt. {health.formula.note}
          </p>
        ) : null}
        </details>
      </div>
    </main>
  );
}
