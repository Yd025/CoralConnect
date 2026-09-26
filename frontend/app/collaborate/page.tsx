"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { joinSession, openCollaborate } from "@/lib/api";
import { BUILDS, CARES, personLine } from "@/lib/connection";
import { useSession } from "@/lib/useSession";

export default function CollaboratePage() {
  const router = useRouter();
  const [code, setCode] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [builds, setBuilds] = useState("");
  const [cares, setCares] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { session, connected } = useSession(code);

  useEffect(() => {
    let stop = false;
    openCollaborate()
      .then((data) => {
        if (!stop) setCode(data.session.code);
      })
      .catch((err: Error) => {
        if (!stop) setError(err.message);
      });
    return () => {
      stop = true;
    };
  }, []);

  const roster = session?.players.filter((player) => player.id !== "p_rehearsal") ?? [];
  const waiting = session?.squads.filter((squad) => squad.playerIds.length < 2).length ?? 0;
  const paired = session?.squads.filter((squad) => squad.creature).length ?? 0;

  async function onJoin(event: FormEvent) {
    event.preventDefault();
    if (!code) return;
    setBusy(true);
    setError(null);
    try {
      const joined = await joinSession(code, name, builds, cares);
      const next = { playerId: joined.player.id, playerToken: joined.playerToken, name: joined.player.name };
      window.localStorage.setItem(`coral-player:${code}`, JSON.stringify(next));
      router.push(`/play/${code}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not join.");
      setBusy(false);
    }
  }

  return (
    <main className="phone">
      <div className="topbar">
        <a className="brand" href="/">CoralConnect</a>
        <span className={connected ? "pill is-live" : "pill"}>{connected ? "Live" : "Connecting"}</span>
      </div>
      <p className="eyebrow">Find a pair</p>
      <h1>Wait here for someone else.</h1>
      <p className="muted">
        This room is open. You do not need a booth code or an admin. When a second person joins, you both get the same animal and find each other.
      </p>
      {error ? <p className="error">{error}</p> : null}

      <section className="panel stack">
        <p className="eyebrow">{code ? `Room ${code}` : "Opening the room"}</p>
        <strong>{roster.length} {roster.length === 1 ? "person" : "people"} here</strong>
        <p className="muted">
          {waiting} waiting for a pair. {paired} {paired === 1 ? "pair is" : "pairs are"} already together.
        </p>
        {roster.length === 0 ? (
          <p className="muted">Nobody is waiting yet. You can be the first.</p>
        ) : (
          <ul className="connection-people">
            {(session?.squads ?? []).map((squad) => {
              const members = squad.playerIds
                .map((id) => roster.find((player) => player.id === id))
                .filter((player) => Boolean(player));
              return (
                <li key={squad.id}>
                  {squad.creature ? squad.creature : "Waiting"}
                  {" · "}
                  {members.map((player) => `${player!.name} · ${personLine(player!.builds, player!.cares)}`).join(" and ")
                    || "Looking for a second person"}
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <form className="panel stack" onSubmit={onJoin}>
        <label>
          Your name
          <input value={name} onChange={(event) => setName(event.target.value)} maxLength={20} required />
        </label>
        <fieldset className="chips">
          <legend>You build</legend>
          {BUILDS.map((item) => (
            <button key={item} type="button" className={builds === item ? "is-on" : ""} onClick={() => setBuilds(item)}>
              {item}
            </button>
          ))}
        </fieldset>
        <fieldset className="chips">
          <legend>You care about</legend>
          {CARES.map((item) => (
            <button key={item} type="button" className={cares === item ? "is-on" : ""} onClick={() => setCares(item)}>
              {item}
            </button>
          ))}
        </fieldset>
        <button className="btn" disabled={busy || !code || !builds || !cares}>
          {busy ? "Joining…" : "Join and wait"}
        </button>
      </form>
    </main>
  );
}
