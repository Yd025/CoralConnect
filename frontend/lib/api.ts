import type { GameSession, Health, Identity, Mode, Submission } from "./types";

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

export function createSession(mode: Mode, challengeId: string) {
  return request<{ adminToken: string; session: GameSession }>("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ mode, challengeId }),
  });
}

export function getSession(code: string): Promise<GameSession> {
  return request<{ session: GameSession }>(`/api/sessions/${code}`).then((data) => data.session);
}

export function joinSession(code: string, name: string, language: string) {
  return request<{ playerToken: string; player: { id: string; name: string }; session: GameSession }>(
    `/api/sessions/${code}/join`,
    { method: "POST", body: JSON.stringify({ name, language }) },
  );
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

export function simulate(code: string, adminToken: string, kind: "efficient" | "bloated") {
  return request<{ session: GameSession; submission: Submission }>(`/api/sessions/${code}/simulate`, {
    method: "POST",
    headers: { "X-Admin-Token": adminToken },
    body: JSON.stringify({ kind }),
  });
}
