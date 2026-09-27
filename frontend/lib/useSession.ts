"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getSession, wsUrl } from "./api";
import type { GameSession, Identity, ReefEvent } from "./types";

// identity: the player on this phone, if any. The socket tells the server who
// it is, so a phone that closes (or walks away) stops holding a room open.
export function useSession(code: string | null, identity: Identity | null = null) {
  const [session, setSession] = useState<GameSession | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [liveEvent, setLiveEvent] = useState<ReefEvent | null>(null);
  const seen = useRef(new Set<string>());
  const hydrated = useRef(false);
  const revision = useRef(0);
  const socketRef = useRef<WebSocket | null>(null);
  const identityRef = useRef<Identity | null>(identity);
  identityRef.current = identity;

  const sayHello = useCallback(() => {
    const socket = socketRef.current;
    const who = identityRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN || !who) return;
    socket.send(JSON.stringify({ type: "hello", playerId: who.playerId, playerToken: who.playerToken }));
  }, []);

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
        if (stop) return;
        setConnected(true);
        sayHello();
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
  }, [code, ingest, sayHello]);

  // Joining happens after the socket is open, so say hello again when the identity arrives.
  useEffect(() => {
    sayHello();
  }, [identity?.playerId, identity?.playerToken, sayHello]);

  const sendDraft = useCallback((playerId: string, playerToken: string, text: string) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: "draft", playerId, playerToken, text }));
  }, []);

  return { session, connected, error, liveEvent, sendDraft, ingest };
}
