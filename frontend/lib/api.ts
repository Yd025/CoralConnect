import type { ChatMessage, GameSession, Health, Identity, JudgeResult, Mode, Submission } from "./types";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function apiBase(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL;
  if (fromEnv) return fromEnv.replace(/\/$/, "");
  if (typeof window === "undefined") return "http://localhost:8080";
  const protocol = window.location.protocol === "https:" ? "https:" : "http:";
  const port = window.location.port;
  if (port === "" || port === "80" || port === "443") {
    return `${protocol}//${window.location.host}`;
  }
  return `${protocol}//${window.location.hostname}:8080`;
}

export function wsUrl(code: string): string {
  return `${apiBase().replace(/^http/, "ws")}/ws/${encodeURIComponent(code)}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    const headers = new Headers(init?.headers);
    if (init?.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    response = await fetch(`${apiBase()}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, `Can't reach the carbon engine at ${apiBase()}. Start the backend on port 8080.`);
  }
  const data = (await response.json().catch(() => ({}))) as { error?: string };
  if (!response.ok) {
    throw new ApiError(response.status, data.error || "Request failed.");
  }
  return data as T;
}

export function getHealth(): Promise<Health> {
  return request<Health>("/api/health");
}

export function getChallenges(): Promise<{ challenges: GameSession["challenge"][] }> {
  return request("/api/challenges");
}

export function openCollaborate() {
  return request<{ session: GameSession }>("/api/collaborate");
}

export function createSession(mode: Mode, challengeId: string) {
  return request<{ adminToken: string; session: GameSession }>("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ mode, challengeId }),
  });
}

export function getSession(code: string): Promise<GameSession> {
  return request<{ session: GameSession }>(`/api/sessions/${code}`).then((data) => data.session);
}

export function joinSession(code: string, name: string, builds: string, cares: string) {
  return request<{ playerToken: string; player: { id: string; name: string }; session: GameSession }>(
    `/api/sessions/${code}/join`,
    { method: "POST", body: JSON.stringify({ name, builds, cares }) },
  );
}

export type ResultCard = {
  id: string;
  kind: Mode;
  names: string[];
  detail: string;
  score: number;
  grade: string;
  challenge: string;
  room: string;
  team?: string;
  createdAt: number;
};

export function getCard(id: string) {
  return request<{ card: ResultCard }>(`/api/cards/${encodeURIComponent(id)}`);
}

export function getPairs() {
  return request<{ pairs: ResultCard[] }>("/api/pairs");
}

export function tapStart(code: string, identity: Identity) {
  return request<{ session: GameSession }>(`/api/sessions/${encodeURIComponent(code)}/ready`, {
    method: "POST",
    body: JSON.stringify({ playerId: identity.playerId, playerToken: identity.playerToken }),
  });
}

export function leaveSession(code: string, identity: Identity) {
  return request<{ session: GameSession }>(`/api/sessions/${code}/leave`, {
    method: "POST",
    body: JSON.stringify({ playerId: identity.playerId, playerToken: identity.playerToken }),
  });
}

export function startSession(code: string, adminToken: string) {
  return request<{ session: GameSession }>(`/api/sessions/${code}/start`, {
    method: "POST",
    headers: { "X-Admin-Token": adminToken },
  });
}

export function endSession(code: string, adminToken: string) {
  return request<{ session: GameSession }>(`/api/sessions/${code}/end`, {
    method: "POST",
    headers: { "X-Admin-Token": adminToken },
  });
}

export function setChallenge(code: string, adminToken: string, challengeId: string) {
  return request<{ session: GameSession }>(`/api/sessions/${code}/challenge`, {
    method: "POST",
    headers: { "X-Admin-Token": adminToken },
    body: JSON.stringify({ challengeId }),
  });
}

export function submitPrompt(code: string, identity: Identity, prompt: string) {
  return request<{ session: GameSession; submission: Submission }>(`/api/sessions/${code}/submit`, {
    method: "POST",
    body: JSON.stringify({
      playerId: identity.playerId,
      playerToken: identity.playerToken,
      prompt,
    }),
  });
}

export type RehearsalKind = "efficient" | "bloated" | "vague";

export type JudgeRequest = {
  prompt: string;
  mode?: "fast" | "full";
  context?: { challengeId?: string; turn?: number; history?: ChatMessage[]; gameMode?: Mode };
};

// The same judge the plugin calls. Fast mode is free and instant, so the phone
// can call it while someone types.
export function judgePrompt(body: JudgeRequest, signal?: AbortSignal) {
  return request<JudgeResult>("/api/judge", {
    method: "POST",
    body: JSON.stringify({ mode: "fast", ...body }),
    signal,
  });
}

export function nextGroup(code: string, adminToken: string) {
  return request<{ session: GameSession }>(`/api/sessions/${code}/next-group`, {
    method: "POST",
    headers: { "X-Admin-Token": adminToken },
  });
}

export function simulate(code: string, adminToken: string, kind: RehearsalKind) {
  return request<{ session: GameSession; submission: Submission }>(`/api/sessions/${code}/simulate`, {
    method: "POST",
    headers: { "X-Admin-Token": adminToken },
    body: JSON.stringify({ kind }),
  });
}
