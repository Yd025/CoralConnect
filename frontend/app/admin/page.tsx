"use client";

import { QRCodeSVG } from "qrcode.react";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatedBackground } from "@/components/AnimatedBackground";
import { createSession, endSession, getChallenges, setChallenge, startSession } from "@/lib/api";
import { playUrl, stageUrl, useBoothOrigin } from "@/lib/booth";
import { personLine } from "@/lib/connection";
import { reefLabel } from "@/lib/reef";
import type { Challenge } from "@/lib/types";
import { useSession } from "@/lib/useSession";

const ADMIN_KEY = "coral-admin";

type SavedAdmin = { code: string; adminToken: string };

export default function AdminPage() {
  const router = useRouter();
  const { origin, host, updateHost } = useBoothOrigin();
  const [challenges, setChallenges] = useState<Challenge[]>([]);
  const [challengeId, setChallengeId] = useState("farm-water");
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
    getChallenges()
      .then((data) => {
        const list = (data.challenges ?? []).filter((item): item is Challenge => Boolean(item));
        setChallenges(list);
        setChallengeId((current) => (list.some((item) => item.id === current) ? current : list[0]?.id ?? current));
      })
      .catch(() => undefined);
  }, []);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (saved) return;
    setBusy(true);
    setError(null);
    try {
      const created = await createSession("compete", challengeId);
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
  const roster = session?.players.filter((player) => player.id !== "p_rehearsal") ?? [];
  const playerMin = session?.playerMin ?? (session?.mode === "collaborate" ? 2 : 1);
  const playerMax = session?.playerMax ?? (session?.mode === "collaborate" ? 8 : 10);
  const canStart = session?.mode === "compete" && session.status === "lobby" && roster.length >= playerMin && roster.length <= playerMax;

  useEffect(() => {
    if (session?.status === "ended" && saved?.code) {
      router.push(`/compete/${saved.code}`);
    }
  }, [router, saved?.code, session?.status]);

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
          <section className="panel admin-desk" aria-labelledby="admin-title">
            <div>
              <p className="hero-kicker"><i />Booth console</p>
              <h1 id="admin-title">Open a compete room.</h1>
              <p className="lede">One live round, up to 10 people, each prompting alone.</p>
            </div>
            {error ? <p className="error">{error}</p> : null}
            <form className="stack" onSubmit={onCreate}>
              <label>
                Challenge
                <select value={challengeId} onChange={(event) => setChallengeId(event.target.value)}>
                  {(challenges.length ? challenges : [{ id: "farm-water", title: "The thirsty farm", brief: "", hint: "", turnCount: 2, targetTokens: 200, beats: [] }]).map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.title} · {item.turnCount || item.beats.length || 2} turns
                    </option>
                  ))}
                </select>
              </label>
              {saved ? null : (
                <button className="btn" disabled={busy} type="submit">
                  Create game and QR
                </button>
              )}
            </form>
            {saved && session ? (
              <div className="admin-desk__foot">
                <div className="health-inline">
                  <span>{reefLabel(session.reefBand)} · reef {session.reefHealth}</span>
                  <i><b style={{ width: `${session.reefHealth}%` }} /></i>
                </div>
                <div className="btn-row">
                  <button className="btn" type="button" disabled={busy || !canStart} onClick={() => run(() => startSession(saved.code, saved.adminToken))}>
                    Start round
                  </button>
                  <button className="btn btn-ghost" type="button" disabled={busy || session.status !== "playing"} onClick={() => run(() => setChallenge(saved.code, saved.adminToken, challengeId))}>
                    Apply challenge
                  </button>
                  <button className="btn btn-danger" type="button" disabled={busy || session.status === "ended"} onClick={() => run(() => endSession(saved.code, saved.adminToken))}>
                    End game
                  </button>
                </div>
              </div>
            ) : null}
          </section>

          <section className="panel admin-join" aria-label="Join this room">
            {!saved || !session ? (
              <p className="muted admin-join__empty">The join code shows up here.</p>
            ) : (
              <>
                <div className="code-block">
                  <div>
                    <p className="eyebrow">
                      Compete · {session.status === "lobby" ? "waiting to start" : session.status}
                    </p>
                    <strong>{session.code}</strong>
                  </div>
                  {play ? (
                    <div className="qr-card">
                      <QRCodeSVG value={play} size={148} bgColor="#f4fff9" fgColor="#042630" />
                    </div>
                  ) : null}
                </div>
                <label>
                  Phone link host
                  <input value={host} onChange={(event) => updateHost(event.target.value)} />
                </label>
                <p className="link-line">{play}</p>
                <div className="btn-row">
                  <button className="btn btn-ghost" type="button" onClick={() => copy(play, "play")}>
                    {copied === "play" ? "Copied" : "Copy join link"}
                  </button>
                  <button className="btn" type="button" onClick={() => window.open(stage, "coral-stage")}>
                    Open main stage
                  </button>
                </div>
                <div className="admin-roster">
                  <h2>Players · {roster.length} / {playerMax}</h2>
                  {roster.length >= playerMax ? <p className="muted">This room is full.</p> : null}
                  {roster.length === 0 ? (
                    <p className="muted">Nobody has joined yet.</p>
                  ) : (
                    <ul className="roster">
                      {roster.map((player) => (
                        <li key={player.id}>
                          <span>
                            <strong>{player.name}</strong>
                            <small>{personLine(player.builds, player.cares)}{player.connected ? "" : " · left"}</small>
                          </span>
                          <b>{player.score}</b>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
