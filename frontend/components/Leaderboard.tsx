import { GradeBadge } from "@/components/GradeBadge";
import { personLine } from "@/lib/connection";
import type { GameSession, Player } from "@/lib/types";

export function Leaderboard({ session, compact = false }: { session: GameSession; compact?: boolean }) {
  const roster = session.players.filter((player) => player.id !== "p_rehearsal");
  const connecting = session.mode === "collaborate";
  const rows = connecting
    ? session.squads.length > 0
      ? session.squads
          .map((squad) => {
            const members = squad.playerIds
              .map((id) => session.players.find((player) => player.id === id))
              .filter((player): player is Player => Boolean(player));
            return {
              id: squad.id,
              name: squad.creature || squad.name || squad.memberNames.join(" · "),
              detail: members.map((player) => personLine(player.builds, player.cares)).join("  ×  "),
              why: [squad.shared, squad.distinct].filter(Boolean).join(" "),
              score: squad.score,
              grade: squad.lastGrade,
            };
          })
          .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name))
      : roster
          .map((player) => ({
            id: player.id,
            name: player.name,
            detail: personLine(player.builds, player.cares),
            why: "Waiting to be matched.",
            score: player.score,
            grade: player.lastGrade,
          }))
          .sort((a, b) => a.name.localeCompare(b.name))
    : roster
        .map((player) => ({
          id: player.id,
          name: player.name,
          detail: personLine(player.builds, player.cares),
          why: "",
          score: player.score,
          grade: player.lastGrade,
        }))
        .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));

  return (
    <section className={compact ? "board board-compact" : "board"}>
      <header className="board__head">
        <h2>{connecting ? "Who's connecting" : "Carbon efficiency"}</h2>
        <p>
          {connecting
            ? "Same animal, same pair. Find that person in the room."
            : "Higher means the model did less extra work."}
        </p>
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
                {row.why ? <small className="connection-why">{row.why}</small> : null}
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
