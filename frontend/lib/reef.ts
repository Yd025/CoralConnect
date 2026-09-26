import type { ReefBand } from "./types";

export function reefLabel(band: ReefBand): string {
  switch (band) {
    case "thriving":
      return "Thriving";
    case "stressed":
      return "Stressed";
    case "bleaching":
      return "Bleaching";
    default:
      return "Collapse";
  }
}

export function estimateTokens(text: string): number {
  const trimmed = text.trim();
  if (!trimmed) return 0;
  return Math.max(1, Math.ceil(trimmed.length / 4));
}

export function slot(id: string): number {
  let hash = 0;
  for (const char of id) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  return 8 + (hash % 76);
}
