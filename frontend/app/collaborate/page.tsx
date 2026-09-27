"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { joinSession, leaveSession, openCollaborate } from "@/lib/api";
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
      .then(async (data) => {
        if (stop) return;
        const room = data.session.code;
        const raw = window.localStorage.getItem(`coral-player:${room}`);
        if (raw) {
          try {
            const saved = JSON.parse(raw) as { playerId?: string; playerToken?: string; name?: string };
            const squad = data.session.squads.find((item) => saved.playerId && item.playerIds.includes(saved.playerId));
            if (saved.playerId && saved.playerToken && squad && !squad.scored) {
              router.replace(`/play/${room}`);
              return;
            }
            if (saved.playerId && saved.playerToken && squad?.scored) {
              await leaveSession(room, { playerId: saved.playerId, playerToken: saved.playerToken, name: saved.name || "" });
            }
          } catch {
            /* A finished phone fills in a new name instead of reopening the old pair. */
          }
          window.localStorage.removeItem(`coral-player:${room}`);
        }
        if (!stop) setCode(room);
      })
      .catch((err: Error) => {
        if (!stop) setError(err.message);
      });
    return () => {
      stop = true;
    };
  }, [router]);

  const roster = session?.players.filter((player) => player.id !== "p_rehearsal") ?? [];
  const openSquads = session?.squads.filter((squad) => !squad.scored) ?? [];
  const waiting = openSquads.filter((squad) => squad.playerIds.length < 2).length;
  const paired = openSquads.filter((squad) => squad.creature).length;

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
        No booth code and no host. Answer two taps. We pair you with someone waiting who builds the same kind of thing or cares about the same thing. You both get the same animal. Find that person, then both tap Start. You have 2 minutes. When you finish, you can pair again. The pair board at /pairs keeps every result.
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
            {openSquads.map((squad) => {
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
