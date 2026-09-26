import type { Grade } from "@/lib/types";

const TONE: Record<Grade, string> = {
  "A+": "grade-ap",
  A: "grade-a",
  B: "grade-b",
  C: "grade-c",
  D: "grade-d",
  F: "grade-f",
};

export function GradeBadge({ grade }: { grade: Grade | null }) {
  if (!grade) return <span className="grade grade-empty">–</span>;
  return <span className={`grade ${TONE[grade]}`}>{grade}</span>;
}
