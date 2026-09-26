"use client";

import { useParams } from "next/navigation";
import { ReefStage } from "@/components/reef/ReefStage";
import { playUrl, useBoothOrigin } from "@/lib/booth";
import { useSession } from "@/lib/useSession";

export default function StagePage() {
  const params = useParams<{ code: string }>();
  const code = String(params.code || "").toUpperCase();
  const { session, error, connected, liveEvent } = useSession(code);
  const { origin } = useBoothOrigin();
  const link = origin ? playUrl(origin, code) : "";

  if (!session) {
    return (
      <main className="stage-page">
        <section className="shell">
          <p className="eyebrow">Main stage</p>
          <h1>{error || "Filling the tank…"}</h1>
          <p className="muted">{connected ? "Connected" : "Reconnecting"} · {code}</p>
        </section>
      </main>
    );
  }

  return (
    <main className="stage-page">
      <ReefStage session={session} liveEvent={liveEvent} playLink={link} />
    </main>
  );
}
