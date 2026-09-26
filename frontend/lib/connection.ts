export const BUILDS = ["Apps", "Data", "Systems", "Hardware", "Design"] as const;
export const CARES = ["People", "Planet", "Trust", "Speed", "Cost"] as const;

export function personLine(builds: string, cares: string) {
  if (builds && cares) return `${builds} · ${cares}`;
  return builds || cares || "Not set";
}
