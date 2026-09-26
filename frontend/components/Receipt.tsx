import type { Submission } from "@/lib/types";

// The bill for one turn: what the message carried, what the model had to go
// look up, and the total the grade came from. Rows come from backend/app/grading.py.
export function Receipt({ submission }: { submission: Submission }) {
  const lines = submission.receipt ?? [];
  if (lines.length === 0) return null;
  const total = submission.effectiveTokens || submission.tokenCount + submission.lookupTokens;
  return (
    <div className="receipt" aria-label="What this turn cost">
      <ul>
        {lines.map((line, index) => (
          <li key={`${line.tone}-${index}`} className={`receipt__line is-${line.tone}`}>
            <span>{line.text}</span>
            {line.tokens ? <b>{line.tone === "cost" ? `+${line.tokens.toLocaleString()}` : line.tokens.toLocaleString()}</b> : null}
          </li>
        ))}
      </ul>
      <p className="receipt__total">
        <span>Tokens the model handled</span>
        <b>
          {total.toLocaleString()} <small>/ {submission.targetTokens} budget</small>
        </b>
      </p>
    </div>
  );
}
