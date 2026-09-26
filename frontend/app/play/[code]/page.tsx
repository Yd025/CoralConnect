"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { GradeBadge } from "@/components/GradeBadge";
import { Leaderboard } from "@/components/Leaderboard";
import { leaveSession, joinSession, submitPrompt } from "@/lib/api";
import { BUILDS, CARES } from "@/lib/connection";
import { estimateTokens } from "@/lib/reef";
import type { Identity, Submission, Thread } from "@/lib/types";
import { useSession } from "@/lib/useSession";

export default function PlayPage() {
  const params = useParams<{ code: string }>();
  const code = String(params.code || "").toUpperCase();
  const { session, connected, error, sendDraft, ingest } = useSession(code);
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [name, setName] = useState("");
  const [builds, setBuilds] = useState("");
  const [cares, setCares] = useState("");
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [latest, setLatest] = useState<Submission | null>(null);
  const draftTimer = useRef<number | null>(null);
  const sawPrompt = useRef(false);

  useEffect(() => {
    const raw = window.localStorage.getItem(storageKey(code));
    if (!raw) return;
    try {
      setIdentity(JSON.parse(raw) as Identity);
    } catch {
      window.localStorage.removeItem(storageKey(code));
    }
  }, [code]);

  useEffect(() => {
    if (!session || !identity) return;
    if (!session.players.some((player) => player.id === identity.playerId)) {
      window.localStorage.removeItem(storageKey(code));
      setIdentity(null);
    }
  }, [session, identity, code]);

  const roster = session?.players.filter((player) => player.id !== "p_rehearsal") ?? [];
  const playerMax = session?.playerMax ?? (session?.mode === "collaborate" ? 8 : 10);
  const tableFull = roster.length >= playerMax;
  const me = session?.players.find((player) => player.id === identity?.playerId);
  const squad = session?.squads.find((item) => item.id === me?.squadId);
  const squadMates = squad
    ? session?.players.filter((player) => squad.playerIds.includes(player.id)) ?? []
    : [];
  const partner = squadMates.find((player) => player.id !== identity?.playerId);
  const paired = session?.mode !== "collaborate" || squadMates.length >= 2;
  const canPlay = session?.mode === "collaborate" ? paired && session.status !== "ended" : session?.status === "playing";
  const ownerId = session?.mode === "collaborate" ? me?.squadId : identity?.playerId;
  const thread = session?.threads?.find((item) => item.ownerId === ownerId) ?? null;
  const beat = session?.challenge?.beats?.[thread?.step ?? 0];
  const turnCount = session?.challenge?.turnCount ?? session?.challenge?.beats?.length ?? 1;
  const turnNumber = Math.min((thread?.step ?? 0) + 1, turnCount);

  useEffect(() => {
    if (!squad || !identity) return;
    if (!sawPrompt.current) {
      setPrompt(squad.prompt);
      sawPrompt.current = true;
      return;
    }
    if (squad.promptAuthorId && squad.promptAuthorId !== identity.playerId) {
      setPrompt(squad.prompt);
    }
  }, [squad, identity]);

  const remembered = useMemo(() => {
    if (!session || !identity) return null;
    return session.submissions.find((item) =>
      session.mode === "collaborate" ? item.squadId && item.squadId === me?.squadId : item.playerId === identity.playerId,
    );
  }, [session, identity, me?.squadId]);

  const shown = latest ?? remembered ?? null;
  const tokens = estimateTokens(prompt);

  async function onJoin(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setLocalError(null);
    try {
      const joined = await joinSession(code, name, builds, cares);
      const next = { playerId: joined.player.id, playerToken: joined.playerToken, name: joined.player.name };
      window.localStorage.setItem(storageKey(code), JSON.stringify(next));
      setIdentity(next);
      ingest(joined.session);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Could not join.");
    } finally {
      setBusy(false);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!identity) return;
    setBusy(true);
    setLocalError(null);
    try {
      const result = await submitPrompt(code, identity, prompt);
      setLatest(result.submission);
      setPrompt("");
      ingest(result.session);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Submit failed.");
    } finally {
      setBusy(false);
    }
  }

  function onPrompt(value: string) {
    setPrompt(value);
    if (session?.mode !== "collaborate" || !identity) return;
    if (draftTimer.current) window.clearTimeout(draftTimer.current);
    const current = identity;
    draftTimer.current = window.setTimeout(() => {
      sendDraft(current.playerId, current.playerToken, value);
    }, 90);
  }

  const piece = session?.mode === "collaborate" ? me?.piece : null;
  const sourceTitle = piece?.title ?? beat?.fixtureTitle;
  const sourceBody = piece?.body ?? beat?.fixture;

  function includeSource() {
    if (!sourceBody) return;
    const next = prompt.trim() ? `${prompt.trim()}\n\n${sourceBody}` : sourceBody;
    onPrompt(next);
  }

  return (
    <main className="phone">
      <div className="topbar">
        <a className="brand" href="/">CoralConnect</a>
        <span className={connected ? "pill is-live" : "pill"}>{connected ? "Live" : "Reconnecting"}</span>
      </div>
      <p className="eyebrow">Game {code}</p>
      {error || localError ? <p className="error">{localError || error}</p> : null}
      {!session ? <p className="muted">Looking for this reef…</p> : null}

      {session ? (
        <>
          <section className="panel stack">
            <h1>{session.challenge?.title}</h1>
            <p>{session.challenge?.brief}</p>
            <p className="muted">
              Turn {turnNumber} of {turnCount}. {session.challenge?.hint}
            </p>
            <div className="health-inline">
              <span>Shared reef · {session.reefHealth}</span>
              <i><b style={{ width: `${session.reefHealth}%` }} /></i>
            </div>
          </section>

          {!identity && tableFull ? (
            <section className="panel stack">
              <h2>This table is full.</h2>
              <p className="muted">
                {session.mode === "collaborate"
                  ? "This room holds 8 players, two to a pair."
                  : "Compete holds up to 10 players."}
              </p>
            </section>
          ) : null}

          {!identity && !tableFull ? (
            <form className="panel stack" onSubmit={onJoin}>
              <label>
                Your name
                <input value={name} onChange={(event) => setName(event.target.value)} maxLength={20} required />
              </label>
              <fieldset className="chips">
                <legend>You build</legend>
                {BUILDS.map((item) => (
                  <button
                    key={item}
                    type="button"
                    className={builds === item ? "is-on" : ""}
                    onClick={() => setBuilds(item)}
                  >
                    {item}
                  </button>
                ))}
              </fieldset>
              <fieldset className="chips">
                <legend>You care about</legend>
                {CARES.map((item) => (
                  <button
                    key={item}
                    type="button"
                    className={cares === item ? "is-on" : ""}
                    onClick={() => setCares(item)}
                  >
                    {item}
                  </button>
                ))}
              </fieldset>
              <button className="btn" disabled={busy || !builds || !cares}>
                Join the reef
              </button>
            </form>
          ) : null}

          {identity && session.status === "lobby" && session.mode !== "collaborate" ? (
            <section className="panel stack">
              <h2>You're in, {identity.name}.</h2>
              <p>This is one round for the room, up to 10 people. It starts when the table says go.</p>
              <p className="muted">{roster.length} of {playerMax} here.</p>
              <button
                className="btn-ghost"
                type="button"
                onClick={() => {
                  void leaveSession(code, identity).then((data) => ingest(data.session));
                  window.localStorage.removeItem(storageKey(code));
                  setIdentity(null);
                }}
              >
                Leave lobby
              </button>
            </section>
          ) : null}

          {identity && session.mode === "collaborate" ? (
            <section className="panel beacon">
              {paired && squad?.creature ? (
                <>
                  <p className="eyebrow">Find your pair</p>
                  <strong>{squad.creature}</strong>
                  <p>Ask who else has {squad.creature} on their phone. Your pair can start now. The rest of the room does not wait.</p>
                  {partner ? (
                    <p className="muted">They build {partner.builds} and care about {partner.cares}.</p>
                  ) : null}
                  {squad.shared ? <p>{squad.shared}</p> : null}
                </>
              ) : (
                <>
                  <p className="eyebrow">Find your pair</p>
                  <strong>Looking</strong>
                  <p>Hold your phone up. The next person in shares your animal. Other pairs can already be playing.</p>
                </>
              )}
              {squad?.promptAuthorId && squad.promptAuthorId !== identity.playerId ? (
                <p className="muted">Your pair just changed the prompt.</p>
              ) : null}
              {session.status === "lobby" ? (
                <button
                  className="btn-ghost"
                  type="button"
                  onClick={() => {
                    void leaveSession(code, identity).then((data) => ingest(data.session));
                    window.localStorage.removeItem(storageKey(code));
                    setIdentity(null);
                  }}
                >
                  Leave lobby
                </button>
              ) : null}
            </section>
          ) : null}

          {identity && paired && session.mode === "collaborate" && squad?.closing && (thread?.done || session.status === "ended") ? (
            <section className="panel beacon">
              <p className="eyebrow">Talk about the environment</p>
              <p>{squad.closing}</p>
            </section>
          ) : null}

          {identity && session.status === "playing" && thread?.done && session.mode !== "collaborate" ? (
            <p className="panel">This thread is closed. Both turns are on the reef.</p>
          ) : null}

          {identity && canPlay && !thread?.done ? (
            <form className="stack" onSubmit={onSubmit}>
              {beat ? (
                <section className="panel stack">
                  {piece ? <p className="eyebrow">{piece.role}</p> : null}
                  <p className="eyebrow">{sourceTitle}</p>
                  <p>{beat.ask}</p>
                  <pre className="fixture">{sourceBody}</pre>
                  <button className="btn-ghost" type="button" onClick={includeSource}>
                    {piece ? "Include your piece" : "Include this source"}
                  </button>
                </section>
              ) : null}
              <label>
                {session.mode === "collaborate" ? "Shared message" : "Your message"}
                <textarea value={prompt} onChange={(event) => onPrompt(event.target.value)} />
              </label>
              <p className="muted">
                {session.mode === "collaborate" && squad
                  ? "Your partner has a different piece. The shared message needs both."
                  : `About ${tokens} tokens in this message. Length is not the grade. A missing source is.`}
              </p>
              <div className="sticky-submit">
                <button className="btn" disabled={busy || !prompt.trim()} type="submit">
                  {busy ? "Asking Grok…" : turnNumber > 1 ? "Send follow-up" : "Send message"}
                </button>
              </div>
            </form>
          ) : null}

          {session.status === "ended" ? <p className="panel">This round is over. Check the big screen for the reef you left behind.</p> : null}

          {shown ? (
            <section className="panel result">
              <div className="code-block">
                <GradeBadge grade={shown.grade} />
                <strong>{shown.score}</strong>
              </div>
              <p className={shown.reasonable ? "verdict is-good" : "verdict is-bad"}>
                {shown.reasonable ? "Reasonable prompt" : "Too much work"}
              </p>
              <p>{shown.verdictReason || shown.summary}</p>
              {shown.judgedByModel ? (
                <p className="muted">A second Grok call read the solver request and graded this prompt.</p>
              ) : null}
              {shown.serverSideTools > 0 ? (
                <p className="muted">That solver call searched the web {shown.serverSideTools} time{shown.serverSideTools === 1 ? "" : "s"}.</p>
              ) : null}
              <p className="muted">The score on the board is the average of your turns. Every turn still changes the reef.</p>
              <pre>{shown.aiResponse}</pre>
            </section>
          ) : null}

          {thread ? <ThreadLog thread={thread} /> : null}
          <Leaderboard session={session} />
        </>
      ) : null}
    </main>
  );
}

function ThreadLog({ thread }: { thread: Thread }) {
  if (thread.messages.length === 0) return null;
  return (
    <section className="panel stack thread-log">
      <h2>This thread</h2>
      {thread.messages.map((message, index) => (
        <p key={`${message.role}-${index}`}>
          <strong>{message.role === "user" ? "You" : "Grok"}</strong>
          {message.content}
        </p>
      ))}
    </section>
  );
}

function storageKey(code: string) {
  return `coral-player:${code}`;
}
