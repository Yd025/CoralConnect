export function TeamMark({ names }: { names: string[] }) {
  const initials = names
    .map((name) => name.trim().charAt(0).toUpperCase())
    .filter(Boolean)
    .slice(0, 2);
  if (initials.length === 0) return null;
  return (
    <span className={initials.length > 1 ? "team-mark" : "team-mark is-one"} aria-hidden="true">
      {initials.map((letter, index) => (
        <span key={`${letter}-${index}`} className={index === 0 ? "team-mark__circle" : "team-mark__circle is-second"}>
          {letter}
        </span>
      ))}
    </span>
  );
}
