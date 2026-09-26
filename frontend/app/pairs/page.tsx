"use client";

import { useEffect, useState } from "react";
import { GradeBadge } from "@/components/GradeBadge";
import { TeamMark } from "@/components/TeamMark";
import { getPairs, type ResultCard } from "@/lib/api";
import type { Grade } from "@/lib/types";

export default function PairsBoardPage() {
  const [pairs, setPairs] = useState<ResultCard[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stop = false;
    async function load() {
      try {
        const data = await getPairs();
        if (!stop) {
          setPairs(data.pairs);
          setError(null);
        }
      } catch (err) {
        if (!stop) setError(err instanceof Error ? err.message : "The pair board is offline.");
      }
    }
    void load();
    const timer = window.setInterval(() => void load(), 3000);
    return () => {
      stop = true;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <main className="phone board-page">
      <div className="topbar">
        <a className="brand" href="/">CoralConnect</a>
        <span className="pill is-live">Live</span>
      </div>
      <p className="eyebrow">Collaboration</p>
      <h1>Every pair</h1>
      <p className="muted">
        This board grows as pairs finish. It is not a competition room. People join from the printed QR on their own phones.
      </p>
      {error ? <p className="error">{error}</p> : null}
      {pairs.length === 0 ? <p className="panel">No finished pairs yet.</p> : null}
      <ol className="podium">
        {pairs.map((pair, index) => (
          <li key={pair.id}>
            <span className="board__rank">{index + 1}</span>
            <span className="board__who">
              <TeamMark names={pair.names} />
              <span>
                <strong className="board__team">{pair.team || pair.names.join(" and ")}</strong>
                <small className="board__members">{pair.names.join(" and ")}</small>
                <small>{pair.challenge}</small>
              </span>
            </span>
            <GradeBadge grade={(pair.grade || null) as Grade | null} />
            <b>{pair.score}</b>
          </li>
        ))}
      </ol>
    </main>
  );
}
