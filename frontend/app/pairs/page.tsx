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

  const ranked = [...pairs].sort((a, b) => b.score - a.score || (a.team || "").localeCompare(b.team || ""));

  return (
    <main className="board-page">
      <header className="standings-top">
        <div className="topbar">
          <a className="brand" href="/">CoralConnect</a>
          <span className="pill is-live">Live</span>
        </div>
        <p className="eyebrow">Pair leaderboard</p>
        <h1>Standings</h1>
        <p className="muted standings-lede">
          Highest prompting score first. A strong pair lands in the 80s. 100 is rare.
        </p>
      </header>
      {error ? <p className="error">{error}</p> : null}
      <section className="standings" aria-label="Pair standings">
        <div className="standings__head">
          <span>Rank</span>
          <span>Team</span>
          <span>Score</span>
        </div>
        {ranked.length === 0 ? (
          <p className="standings__empty">No finished pairs yet. Scores land here when a round ends.</p>
        ) : (
          <ol>
            {ranked.map((pair, index) => (
              <li key={pair.id} className={index < 3 ? `standing is-${index + 1}` : "standing"}>
                <span className="standing__rank">{index + 1}</span>
                <a className="standing__who" href={`/card/${pair.id}`}>
                  <TeamMark names={pair.names} />
                  <span>
                    <strong className="board__team">{pair.team || pair.names.join(" and ")}</strong>
                    <small className="board__members">{pair.names.join(" and ")}</small>
                    <small>{pair.challenge}</small>
                  </span>
                </a>
                <span className="standing__score">
                  <b>{pair.score}</b>
                  <GradeBadge grade={(pair.grade || null) as Grade | null} />
                </span>
              </li>
            ))}
          </ol>
        )}
      </section>
    </main>
  );
}
