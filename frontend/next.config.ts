import type { NextConfig } from "next";
import os from "os";

function lanHosts(): string[] {
  const hosts = new Set<string>(["localhost", "127.0.0.1", "host.docker.internal"]);
  for (const host of (process.env.ALLOWED_DEV_ORIGINS || "").split(",")) {
    const cleaned = host.trim();
    if (cleaned) hosts.add(cleaned);
  }
  for (const nets of Object.values(os.networkInterfaces())) {
    for (const net of nets ?? []) {
      const family = String(net.family);
      if (family === "IPv4" || family === "4") hosts.add(net.address);
    }
  }
  return [...hosts];
}

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  devIndicators: false,
  allowedDevOrigins: lanHosts(),
  async redirects() {
    return [
      { source: "/play", destination: "/", permanent: false },
      { source: "/admin/results/:code", destination: "/compete/:code", permanent: false },
      { source: "/r/:id", destination: "/card/:id", permanent: false },
    ];
  },
};

export default nextConfig;
