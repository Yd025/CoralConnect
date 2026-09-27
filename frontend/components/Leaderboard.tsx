import { GradeBadge } from "@/components/GradeBadge";
import { TeamMark } from "@/components/TeamMark";
import { personLine } from "@/lib/connection";
import type { GameSession, Player } from "@/lib/types";

export function Leaderboard({ session, compact = false }: { session: GameSession; compact?: boolean }) {
  const roster = session.players.filter((player) => player.id !== "p_rehearsal");
  const connecting = session.mode === "collaborate";
  const holdScore = connecting && Boolean(session.challenge?.build);
  const rows = connecting
    ? session.squads.length > 0
      ? session.squads
          .map((squad) => {
            const members = squad.playerIds
              .map((id) => session.players.find((player) => player.id === id))
              .filter((player): player is Player => Boolean(player));
            const names = members.map((player) => player.name);
            return {
              id: squad.id,
              name: squad.creature ? `Team ${squad.creature}` : "Looking",
              detail: names.join(" and "),
              names,
              why: "",
              score: squad.score,
              grade: squad.scored ? squad.lastGrade : null,
              scored: !holdScore || squad.scored,
            };
          })
          .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name))
      : roster
          .map((player) => ({
            id: player.id,
            name: "Looking",
            detail: player.name,
            names: [player.name],
            why: "",
            score: player.score,
            grade: null as Player["lastGrade"],
            scored: !holdScore,
          }))
          .sort((a, b) => a.detail.localeCompare(b.detail))
    : roster
        .map((player) => ({
          id: player.id,
          name: player.name,
          detail: personLine(player.builds, player.cares),
          names: [] as string[],
          why: "",
          score: player.score,
          grade: player.lastGrade,
          scored: true,
        }))
        .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));

  return (
    <section className={compact ? "board board-compact" : "board"}>
      <header className="board__head">
        <h2>{connecting ? "Teams" : "Carbon efficiency"}</h2>
        <p>
          {connecting
            ? "Out of 100. A strong pair lands in the 80s. The number shows up when the round ends."
            : "One round, up to 10. Higher means the model did less extra work."}
        </p>
      </header>
      {rows.length === 0 ? (
        <p className="muted">Waiting for the first player.</p>
      ) : (
        <ol>
          {rows.map((row, index) => (
            <li key={row.id}>
              <span className="board__rank">{index + 1}</span>
              <span className="board__who">
                {row.names.length > 0 ? <TeamMark names={row.names} /> : null}
                <span>
                  <strong className={connecting ? "board__team" : undefined}>{row.name}</strong>
                  {row.detail ? <small className={connecting ? "board__members" : undefined}>{row.detail}</small> : null}
                  {row.why ? <small className="connection-why">{row.why}</small> : null}
                </span>
              </span>
              <GradeBadge grade={row.grade} />
              <b>{row.scored ? row.score : "—"}</b>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
