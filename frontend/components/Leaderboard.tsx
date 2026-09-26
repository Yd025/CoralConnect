import { GradeBadge } from "@/components/GradeBadge";
import type { GameSession } from "@/lib/types";

export function Leaderboard({ session, compact = false }: { session: GameSession; compact?: boolean }) {
  const rows =
    session.mode === "collaborate"
      ? session.squads
          .map((squad) => ({
            id: squad.id,
            name: squad.name,
            detail: squad.memberNames.join(" · "),
            score: squad.score,
            grade: squad.lastGrade,
          }))
          .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name))
      : session.players
          .filter((player) => player.id !== "p_rehearsal")
          .map((player) => ({
            id: player.id,
            name: player.name,
            detail: player.language,
            score: player.score,
            grade: player.lastGrade,
          }))
          .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));

  return (
    <section className={compact ? "board board-compact" : "board"}>
      <header className="board__head">
        <h2>{session.mode === "collaborate" ? "Reef squads" : "Carbon efficiency"}</h2>
        <p>{session.mode === "collaborate" ? "One score for the pair." : "Higher means the model did less extra work."}</p>
      </header>
      {rows.length === 0 ? (
        <p className="muted">Waiting for the first player.</p>
      ) : (
        <ol>
          {rows.map((row, index) => (
            <li key={row.id}>
              <span className="board__rank">{index + 1}</span>
              <span>
                <strong>{row.name}</strong>
                <small>{row.detail}</small>
              </span>
              <GradeBadge grade={row.grade} />
              <b>{row.score}</b>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
