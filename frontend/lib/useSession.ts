"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getSession, wsUrl } from "./api";
import type { GameSession, ReefEvent } from "./types";

export function useSession(code: string | null) {
  const [session, setSession] = useState<GameSession | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [liveEvent, setLiveEvent] = useState<ReefEvent | null>(null);
  const seen = useRef(new Set<string>());
  const hydrated = useRef(false);
  const revision = useRef(0);
  const socketRef = useRef<WebSocket | null>(null);
  const who = useRef<{ playerId: string; playerToken: string } | null>(null);

  const ingest = useCallback((next: GameSession) => {
    if (next.revision < revision.current) return;
    revision.current = next.revision;
    setSession(next);
    setError(null);
    const events = next.events ?? [];
    if (!hydrated.current) {
      events.forEach((event) => seen.current.add(event.id));
      hydrated.current = true;
      return;
    }
    const fresh = events.filter((event) => !seen.current.has(event.id));
    events.forEach((event) => seen.current.add(event.id));
    if (fresh[0]) setLiveEvent(fresh[0]);
  }, []);

  useEffect(() => {
    if (!code) return;
    let stop = false;
    let retry = 0;
    let poll = 0;
    hydrated.current = false;
    seen.current = new Set();
    revision.current = 0;

    const pull = async () => {
      try {
        const next = await getSession(code);
        if (!stop) ingest(next);
      } catch (err) {
        if (!stop) setError(err instanceof Error ? err.message : "Can't reach the game.");
      }
    };

    const connect = () => {
      if (stop) return;
      const socket = new WebSocket(wsUrl(code));
      socketRef.current = socket;
      socket.onopen = () => {
        if (!stop) setConnected(true);
        const mine = who.current;
        if (mine) socket.send(JSON.stringify({ type: "hello", playerId: mine.playerId, playerToken: mine.playerToken }));
      };
      socket.onclose = () => {
        if (stop) return;
        setConnected(false);
        retry = window.setTimeout(connect, 1200);
      };
      socket.onerror = () => socket.close();
      socket.onmessage = (message) => {
        try {
          const data = JSON.parse(String(message.data)) as {
            type?: string;
            session?: GameSession;
            message?: string;
          };
          if (data.type === "state" && data.session) ingest(data.session);
          if (data.type === "error" && data.message) setError(data.message);
        } catch {
          /* Ignore a bad frame and keep the socket. */
        }
      };
    };

    void pull();
    connect();
    poll = window.setInterval(() => void pull(), 4000);

    return () => {
      stop = true;
      window.clearInterval(poll);
      window.clearTimeout(retry);
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [code, ingest]);

  const identify = useCallback((playerId: string, playerToken: string) => {
    who.current = { playerId, playerToken };
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: "hello", playerId, playerToken }));
  }, []);

  return { session, connected, error, liveEvent, identify, ingest };
}
