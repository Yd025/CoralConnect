"use client";

import { useEffect, useState } from "react";
import { getHealth } from "./api";

const HOST_KEY = "coral-host";

function isLocal(host: string) {
  return host === "localhost" || host === "127.0.0.1";
}

export function originFor(host: string) {
  if (typeof window === "undefined") return "";
  const hostName = host.replace(/^https?:\/\//, "").split("/")[0].split(":")[0];
  const isDomain = hostName.includes(".") && !/^\d+(\.\d+){3}$/.test(hostName);
  const samePage = window.location.hostname === hostName;
  if (isDomain && !samePage) return `http://${hostName}`;
  const protocol = window.location.protocol;
  const port = samePage && window.location.port ? `:${window.location.port}` : "";
  return `${protocol}//${hostName}${port}`;
}

export function useBoothOrigin() {
  const [origin, setOrigin] = useState("");
  const [host, setHost] = useState("");

  useEffect(() => {
    let cancel = false;
    const saved = window.localStorage.getItem(HOST_KEY) || "";
    getHealth()
      .then((health) => {
        if (cancel) return;
        const domain = (health.techDomain || "").replace(/^https?:\/\//, "").split("/")[0].split(":")[0];
        const savedHost = saved && !isLocal(saved) ? saved : "";
        const next = domain || savedHost || (isLocal(window.location.hostname) ? health.lanIp : window.location.hostname);
        setHost(next);
        setOrigin(originFor(next));
      })
      .catch(() => {
        if (cancel) return;
        setHost(window.location.hostname);
        setOrigin(window.location.origin);
      });
    return () => {
      cancel = true;
    };
  }, []);

  const updateHost = (next: string) => {
    const cleaned = next.trim();
    setHost(cleaned);
    if (cleaned) {
      window.localStorage.setItem(HOST_KEY, cleaned);
      setOrigin(originFor(cleaned));
    }
  };

  return { origin, host, updateHost };
}

export function playUrl(origin: string, code: string) {
  return `${origin}/play/${code}`;
}

export function stageUrl(origin: string, code: string) {
  return `${origin}/stage/${code}`;
}
