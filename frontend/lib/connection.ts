export function laneLabel(lane: string) {
  return lane === "climate" ? "Climate engineer" : "Software engineer";
}

export function kindLabel(kind: string) {
  if (kind === "bridge") return "Bridge";
  if (kind === "same_mission") return "Same mission";
  return "Open seat";
}

export function personLine(lane: string, focus: string) {
  const label = laneLabel(lane);
  return focus ? `${label} · ${focus}` : label;
}

export function connectionCue(kind: string, lanes: string[]) {
  if (kind === "bridge") {
    return "A climate engineer and a software engineer share this message. Agree on it before you send it.";
  }
  if (lanes.length > 0 && lanes.every((lane) => lane === "climate")) {
    return "You both build for the climate. Compare what you work on, then send one message.";
  }
  return "You both build software. Find what you have in common, then send one message.";
}
