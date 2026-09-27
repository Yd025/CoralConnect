"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { GradeBadge } from "@/components/GradeBadge";
import { Leaderboard } from "@/components/Leaderboard";
import { LiveVerdict } from "@/components/LiveVerdict";
import { Receipt } from "@/components/Receipt";
import { RoundTimer, useRoundRemaining } from "@/components/RoundTimer";
import { reefPresence } from "@/components/reef/FallbackReef";
import { getSession, leaveSession, joinSession, submitPrompt, tapStart } from "@/lib/api";
import { BUILDS, CARES } from "@/lib/connection";
import { estimateTokens } from "@/lib/reef";
import type { Identity, ReefBand, Submission, Thread } from "@/lib/types";
import { useSession } from "@/lib/useSession";

export default function PlayPage() {
  const router = useRouter();
  const params = useParams<{ code: string }>();
  const code = String(params.code || "").toUpperCase();
  const { session, connected, error, identify, ingest } = useSession(code);
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [identityReady, setIdentityReady] = useState(false);
  const [name, setName] = useState("");
  const [builds, setBuilds] = useState("");
  const [cares, setCares] = useState("");
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [latest, setLatest] = useState<Submission | null>(null);
  const [openFile, setOpenFile] = useState("");
  const joining = useRef(false);
  const logRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const raw = window.localStorage.getItem(storageKey(code));
    if (raw) {
      try {
        setIdentity(JSON.parse(raw) as Identity);
      } catch {
        window.localStorage.removeItem(storageKey(code));
      }
    }
    setIdentityReady(true);
  }, [code]);

  useEffect(() => {
    if (!identityReady || !session || !identity) return;
    if (!session.players.some((player) => player.id === identity.playerId)) {
      window.localStorage.removeItem(storageKey(code));
      setIdentity(null);
    }
  }, [identityReady, session, identity, code]);

  useEffect(() => {
    if (!identity) return;
    identify(identity.playerId, identity.playerToken);
  }, [identity, connected, identify]);

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
  const buildRound = Boolean(session?.challenge?.build);
  const started = !buildRound || Boolean(squad?.startedAt);
  const canPlay = session?.mode === "collaborate" ? paired && started && session.status !== "ended" : session?.status === "playing";
  const readyIds = squad?.readyIds ?? [];
  const iAmReady = Boolean(identity && readyIds.includes(identity.playerId));
  const waitingOn = squadMates.find((player) => !readyIds.includes(player.id));
  const ownerId = session?.mode === "collaborate" ? me?.squadId : identity?.playerId;
  const thread = session?.threads?.find((item) => item.ownerId === ownerId) ?? null;
  const projectFiles = thread?.files?.length ? thread.files : session?.challenge?.files ?? [];
  const shownFile = projectFiles.find((file) => file.name === openFile) ?? projectFiles[0];
  const beats = session?.challenge?.beats ?? [];
  const beat = beats[Math.min(thread?.step ?? 0, Math.max(beats.length - 1, 0))];
  const turnCount = thread?.turnLimit || session?.turnsAllowed || session?.challenge?.turnCount || beats.length || 1;
  const turnNumber = Math.min((thread?.step ?? 0) + 1, turnCount);
  const roundSeconds = session?.mode === "compete" ? session.roundSeconds || 90 : 120;
  const clockStart = session?.mode === "compete" ? session.startedAt || 0 : buildRound ? squad?.startedAt || 0 : 0;
  const clockActive = session?.mode === "compete"
    ? session.status === "playing"
    : Boolean(buildRound && started && !thread?.done && session?.status !== "ended");
  const remaining = useRoundRemaining(clockStart, clockActive, roundSeconds);

  useEffect(() => {
    if (!clockStart || !clockActive || remaining == null || remaining > 0) return;
    const timer = window.setTimeout(() => {
      void getSession(code).then(ingest).catch(() => undefined);
    }, 400);
    return () => window.clearTimeout(timer);
  }, [clockStart, clockActive, remaining, code, ingest]);

  const remembered = useMemo(() => {
    if (!session || !identity) return null;
    return session.submissions.find((item) =>
      session.mode === "collaborate" ? item.squadId && item.squadId === me?.squadId : item.playerId === identity.playerId,
    );
  }, [session, identity, me?.squadId]);

  // Show whichever result is newer: mine, or my partner's on our shared thread.
  // On a tie it's the same submission, and the session copy has the latest
  // numbers (the measured better-prompt run lands after the grade).
  const shown =
    latest && remembered ? (remembered.createdAt >= latest.createdAt ? remembered : latest) : latest ?? remembered ?? null;

  async function onJoin(event: FormEvent) {
    event.preventDefault();
    if (joining.current || identity) return;
    joining.current = true;
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
      joining.current = false;
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

  async function onStart() {
    if (!identity) return;
    setBusy(true);
    setLocalError(null);
    try {
      const data = await tapStart(code, identity);
      ingest(data.session);
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Could not start.");
    } finally {
      setBusy(false);
    }
  }

  async function leaveRoom(next: string) {
    if (!identity) return;
    try {
      const data = await leaveSession(code, identity);
      ingest(data.session);
    } catch {
      // The room may already have dropped this phone. Still send them on.
    }
    window.localStorage.removeItem(storageKey(code));
    setIdentity(null);
    router.push(next);
  }

  function onPrompt(value: string) {
    setPrompt(value);
  }

  useEffect(() => {
    const node = logRef.current;
    if (!node) return;
    node.scrollTop = node.scrollHeight;
  }, [thread?.messages.length, shown?.id, busy, session?.status, identity?.playerId, localError]);

  const piece = session?.mode === "collaborate" ? me?.piece : null;
  const sourceTitle = piece?.title ?? beat?.fixtureTitle;
  const sourceBody = piece?.body ?? beat?.fixture;

  function includeSource() {
    if (!sourceBody) return;
    const next = prompt.trim() ? `${prompt.trim()}\n\n${sourceBody}` : sourceBody;
    onPrompt(next);
  }

  const tokens = estimateTokens(prompt);
  const compete = session?.mode === "compete";

  if (compete && session) {
    const ask = beat?.ask;
    return (
      <main className="compete-play">
        <RoundTimer startedAt={session.startedAt} active={session.status === "playing"} seconds={roundSeconds} />
        <CompeteScene band={session.reefBand} health={session.reefHealth} />
        <section className="chat" aria-label="Chat with Grok">
          <header className="chat-head">
            <a className="chat-face" href="/" aria-label="CoralConnect home">
              <img src="/reef/05-otto-octopus.svg" alt="" />
            </a>
            <div className="chat-id">
              <strong>Grok</strong>
              <span>Turn {turnNumber} of {turnCount} · {code}</span>
            </div>
            <div className="chat-health health-inline">
              <span>Reef {session.reefHealth}</span>
              <i><b style={{ width: `${session.reefHealth}%` }} /></i>
            </div>
            <span className={connected ? "pill is-live" : "pill"}>{connected ? "Live" : "Reconnecting"}</span>
          </header>

          <details className="chat-board">
            <summary>Leaderboard</summary>
            <Leaderboard session={session} compact />
          </details>

          <div className="chat-log" ref={logRef}>
            {error || localError ? <p className="error">{localError || error}</p> : null}

            <div className="chat-msg is-grok">
              <span className="chat-msg__who">Grok</span>
              {session.challenge?.title ? <p className="chat-msg__title">{session.challenge.title}</p> : null}
              {session.challenge?.brief ? <p>{session.challenge.brief}</p> : null}
              {session.challenge?.hint ? <p className="muted">{session.challenge.hint}</p> : null}
            </div>

            {ask && sourceBody ? (
              <SourceNote title={sourceTitle} ask={ask} body={sourceBody} onInclude={identity ? includeSource : undefined} />
            ) : null}

            {identityReady && !identity && tableFull ? (
              <div className="chat-msg is-grok">
                <span className="chat-msg__who">Grok</span>
                <p>This table is full. Compete holds up to 10 players.</p>
              </div>
            ) : null}

            {identityReady && !identity && !tableFull ? (
              <form className="chat-join stack" onSubmit={onJoin}>
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

            {identity && session.status === "lobby" ? (
              <div className="chat-msg is-grok">
                <span className="chat-msg__who">Grok</span>
                <p>You're in, {identity.name}. This round starts when the table says go. {roster.length} of {playerMax} here.</p>
                <button className="btn-ghost" type="button" onClick={() => void leaveRoom("/")}>
                  Leave
                </button>
              </div>
            ) : null}

            {thread?.messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={message.role === "user" ? "chat-msg is-you" : "chat-msg is-grok"}
              >
                <span className="chat-msg__who">{message.role === "user" ? "You" : "Grok"}</span>
                <p>{message.content}</p>
              </div>
            ))}

            {shown ? (
              <div className="chat-msg is-grok">
                <span className="chat-msg__who">Grok</span>
                <ResultCard shown={shown} />
              </div>
            ) : null}

            {identity && session.status === "playing" && thread?.done ? (
              <div className="chat-msg is-grok">
                <span className="chat-msg__who">Grok</span>
                <p>This round is finished. Save the card, or leave the room.</p>
                {thread.cardId ? <a className="btn" href={`/card/${thread.cardId}`}>Save this result</a> : null}
                <button className="btn-ghost" type="button" onClick={() => void leaveRoom("/")}>Leave</button>
              </div>
            ) : null}

            {session.status === "ended" ? (
              <div className="chat-msg is-grok">
                <span className="chat-msg__who">Grok</span>
                <p>This round is over. Check the big screen for the reef you left behind.</p>
              </div>
            ) : null}
          </div>

          {identity && canPlay && !thread?.done ? (
            <form className="chat-compose" onSubmit={onSubmit}>
              <textarea
                value={prompt}
                onChange={(event) => onPrompt(event.target.value)}
                placeholder="Message Grok"
                aria-label="Message to Grok"
                rows={2}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    event.currentTarget.form?.requestSubmit();
                  }
                }}
              />
              <button className="btn" disabled={busy || !prompt.trim()} type="submit">
                {busy ? "Sending" : "Send"}
              </button>
              <button className="btn-ghost" type="button" onClick={() => void leaveRoom("/")}>Leave</button>
              <p className="muted">About {tokens} tokens in this message. Length is not the grade. A missing source is.</p>
              <LiveVerdict
                prompt={prompt}
                challengeId={session.challenge?.id}
                mode={session.mode}
                turn={turnNumber}
                history={thread?.messages ?? []}
              />
            </form>
          ) : null}
        </section>
      </main>
    );
  }

  return (
    <main className="phone">
      <RoundTimer startedAt={clockStart} active={clockActive} seconds={roundSeconds} />
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

          {identityReady && !identity && tableFull ? (
            <section className="panel stack">
              <h2>This table is full.</h2>
              <p className="muted">
                {session.mode === "collaborate"
                  ? "This room holds 8 players, two to a pair."
                  : "Compete holds up to 10 players."}
              </p>
            </section>
          ) : null}

          {!identityReady ? <p className="panel">Checking this phone…</p> : null}

          {identityReady && !identity && !tableFull ? (
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
              <p>This is one round for the room, up to 10 people. It starts when the table says go, and you have 1 minute 30 seconds.</p>
              <p className="muted">{roster.length} of {playerMax} here.</p>
              <button className="btn-ghost" type="button" onClick={() => void leaveRoom("/")}>
                Leave
              </button>
            </section>
          ) : null}

          {identity && session.mode === "collaborate" ? (
            <section className="panel beacon">
              {paired && squad?.creature ? (
                <>
                  <p className="eyebrow">{buildRound && started ? "Team" : "Find your pair"}</p>
                  <strong>{buildRound ? `Team ${squad.creature}` : squad.creature}</strong>
                  {buildRound && !started ? (
                    <p>Find {partner?.name ?? "your partner"} in the room. When you are together, both of you tap Start.</p>
                  ) : buildRound && started && !thread?.done ? (
                    <p>Name the file and the function. Grok edits that file.</p>
                  ) : buildRound && thread?.done ? (
                    <p>The round is over.</p>
                  ) : (
                    <p>Ask who else has {squad.creature} on their phone. Your pair can start now. The rest of the room does not wait.</p>
                  )}
                  {partner ? (
                    <p className="muted">{partner.name} builds {partner.builds} and cares about {partner.cares}.</p>
                  ) : null}
                  {squad.shared && !buildRound ? <p>{squad.shared}</p> : null}
                  {buildRound && !started ? (
                    iAmReady ? (
                      <p>Waiting for {waitingOn?.name ?? "your partner"} to tap Start.</p>
                    ) : (
                      <button className="btn" type="button" disabled={busy} onClick={() => void onStart()}>
                        {busy ? "Starting…" : "Start"}
                      </button>
                    )
                  ) : null}
                </>
              ) : (
                <>
                  <p className="eyebrow">Find your pair</p>
                  <strong>Looking</strong>
                  <p>Hold your phone up. The next person in shares your animal. Other pairs can already be playing.</p>
                </>
              )}
              <button className="btn-ghost" type="button" onClick={() => void leaveRoom("/")}>
                Leave
              </button>
            </section>
          ) : null}

          {identity && paired && session.mode === "collaborate" && squad?.closing && (thread?.done || session.status === "ended") ? (
            <section className="panel beacon">
              <p className="eyebrow">Talk about the environment</p>
              {squad.scored ? (
                <p>Team {squad.creature} scored {squad.score} for prompting.</p>
              ) : null}
              <p>{squad.closing}</p>
              {thread?.cardId ? <a className="btn" href={`/card/${thread.cardId}`}>Save this result</a> : null}
              {thread?.done ? (
                <button className="btn" type="button" onClick={() => void leaveRoom("/collaborate")}>
                  Find another pair
                </button>
              ) : null}
            </section>
          ) : null}

          {identity && thread?.done && session.mode !== "collaborate" ? (
            <section className="panel stack">
              <p>This round is finished. Save the card, or leave the room.</p>
              {thread.cardId ? <a className="btn" href={`/card/${thread.cardId}`}>Save this result</a> : null}
              <button className="btn-ghost" type="button" onClick={() => void leaveRoom("/")}>Leave</button>
            </section>
          ) : null}

          {identity && canPlay && !thread?.done ? (
            <form className="stack" onSubmit={onSubmit}>
              {beat ? (
                <section className="panel stack">
                  {piece ? <p className="eyebrow">{piece.role}</p> : null}
                  <p className="eyebrow">{sourceTitle}</p>
                  <p>{beat.ask}</p>
                  {buildRound && piece ? <p>{piece.body}</p> : null}
                  {buildRound && projectFiles.length > 0 ? (
                    <>
                      <div className="file-tabs">
                        {projectFiles.map((file) => (
                          <button
                            className={shownFile?.name === file.name ? "file-tab is-on" : "file-tab"}
                            key={file.name}
                            type="button"
                            onClick={() => setOpenFile(file.name)}
                          >
                            {file.name}
                          </button>
                        ))}
                      </div>
                      {shownFile ? <pre className="fixture">{shownFile.body}</pre> : null}
                    </>
                  ) : (
                    <pre className="fixture">{sourceBody}</pre>
                  )}
                  {piece && !buildRound ? (
                    <button className="btn-ghost" type="button" onClick={includeSource}>
                      Include your piece
                    </button>
                  ) : null}
                  <p className="muted small">
                    {buildRound
                      ? "Your prompt stays on this phone. Name your file, your function, and the rule. Pasting the error is not enough."
                      : piece
                        ? "Your pair can't see this piece. Put in the part the model needs. Pasting all of it costs tokens too."
                        : "Quote the lines the model needs. Long-press to copy from the file. Pasting all of it costs tokens too."}
                  </p>
                </section>
              ) : null}
              <label>
                <span className="play-label">
                  {buildRound ? "Your prompt" : session.mode === "collaborate" ? "Your message" : "Your message"}
                </span>
                <textarea value={prompt} onChange={(event) => onPrompt(event.target.value)} />
              </label>
              {buildRound && squad ? (
                <p className="muted">Your partner types on their own phone. Tell them what you find. The app works when both files are edited.</p>
              ) : session.mode === "collaborate" && squad ? (
                <p className="muted">Your partner has a different piece. The shared message needs both.</p>
              ) : null}
              <LiveVerdict
                prompt={prompt}
                challengeId={session.challenge?.id}
                mode={session.mode}
                turn={turnNumber}
                history={thread?.messages ?? []}
              />
              <div className="sticky-submit">
                <button className="btn" disabled={busy || !prompt.trim()} type="submit">
                  {busy ? "Asking Grok…" : turnNumber > 1 ? "Send follow-up" : "Send message"}
                </button>
              </div>
            </form>
          ) : null}

          {session.status === "ended" ? <p className="panel">This round is over. Check the big screen for the reef you left behind.</p> : null}

          {shown ? <ResultCard shown={shown} /> : null}

          {thread ? <ThreadLog thread={thread} /> : null}
          <Leaderboard session={session} />
        </>
      ) : null}
    </main>
  );
}

function SourceNote({
  title,
  ask,
  body,
  onInclude,
}: {
  title?: string;
  ask: string;
  body: string;
  onInclude?: () => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="chat-msg is-grok">
      <span className="chat-msg__who">Grok</span>
      <p>{ask}</p>
      <button className="btn-ghost" type="button" onClick={() => setOpen((value) => !value)}>
        {open ? "Hide the source" : "See the source"}
      </button>
      {open ? (
        <>
          {title ? <p className="eyebrow">{title}</p> : null}
          <pre className="fixture">{body}</pre>
          {onInclude ? (
            <button className="btn-ghost" type="button" onClick={onInclude}>
              Include this source
            </button>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

function CompeteScene({ band, health }: { band: ReefBand; health: number }) {
  const life = reefPresence(health);
  return (
    <div className="compete-scene" aria-hidden="true">
      <img className="compete-scene__band" src={`/reef/${band}.svg`} alt="" />
      {life.fish ? <span className="swimmer s1 is-flip"><img src="/reef/04-pip-fish.svg" alt="" /></span> : null}
      {life.school ? <span className="swimmer s2"><img src="/reef/04-pip-fish.svg" alt="" /></span> : null}
      {life.jelly ? <span className="swimmer s3"><img src="/reef/03-juno-jellyfish.svg" alt="" /></span> : null}
      {life.whale ? <span className="swimmer s-whale is-flip"><img src="/reef/06-winnie-whale.svg" alt="" /></span> : null}
      {life.bag ? <span className="swimmer s-trash"><img src="/reef/plastic-bag.svg" alt="" /></span> : null}
      {life.bottle ? <span className="swimmer s-trash t2"><img src="/reef/crushed-bottle.svg" alt="" /></span> : null}
      {life.bones ? <span className="swimmer s-trash t3"><img src="/reef/fishbones-small.svg" alt="" /></span> : null}
    </div>
  );
}

function ResultCard({ shown }: { shown: Submission }) {
  const [open, setOpen] = useState(false);
  const problems = !shown.reasonable;
  return (
    <section className="panel result">
      <div className="code-block">
        <GradeBadge grade={shown.grade} />
        <strong>{shown.score}</strong>
      </div>
      <p className={shown.reasonable ? "verdict is-good" : "verdict is-bad"}>
        {shown.reasonable ? "Reasonable prompt" : "Too much work"}
      </p>
      <p>
        {shown.reasonable
          ? "The source was in the message, so Grok did no extra search."
          : "The source was missing, so Grok searched and the reef paid for it."}
      </p>
      <button className="btn-ghost" type="button" onClick={() => setOpen((value) => !value)}>
        {open ? "Hide the details" : problems ? "See the problems" : "See Grok's answer"}
      </button>
      {open ? (
        <div className="result-details stack">
          <p>{shown.verdictReason || shown.summary}</p>
          {shown.savedVsVague > 0 ? (
            <p>This prompt saved {shown.savedVsVague.toLocaleString()} tokens compared with a vague one.</p>
          ) : null}
          <Receipt submission={shown} />
          {shown.betterPrompt ? (
            <div className="better-prompt">
              <p className="eyebrow">Shorter, with every detail</p>
              <p>{shown.betterPrompt}</p>
              <p className="muted">
                {shown.measuredSaved > 0
                  ? `Measured with Grok: ${shown.measuredTokens.toLocaleString()} real tokens for yours, ${shown.betterMeasuredTokens.toLocaleString()} for this one. Saves ${shown.measuredSaved.toLocaleString()}.`
                  : `Saves about ${shown.betterSaves.toLocaleString()} tokens by the judge's count.`}
              </p>
            </div>
          ) : null}
          {shown.judgedByModel ? (
            <p className="muted">A second Grok call reviewed this prompt. It can add cost, never remove it.</p>
          ) : null}
          {shown.serverSideTools > 0 ? (
            <p className="muted">That solver call searched the web {shown.serverSideTools} time{shown.serverSideTools === 1 ? "" : "s"}.</p>
          ) : null}
          <p className="muted">The score on the board is the average of your turns. Every turn still changes the reef.</p>
          <pre>{shown.aiResponse}</pre>
        </div>
      ) : null}
    </section>
  );
}

function ThreadLog({ thread }: { thread: Thread }) {
  const [open, setOpen] = useState(false);
  if (thread.messages.length === 0) return null;
  return (
    <section className="panel stack thread-log">
      <h2>This thread</h2>
      <button className="btn-ghost" type="button" onClick={() => setOpen((value) => !value)}>
        {open ? "Hide the thread" : "See the thread"}
      </button>
      {open
        ? thread.messages.map((message, index) => (
            <p key={`${message.role}-${index}`}>
              <strong>{message.role === "user" ? "You" : "Grok"}</strong>
              {message.content}
            </p>
          ))
        : null}
    </section>
  );
}

function storageKey(code: string) {
  return `coral-player:${code}`;
}
