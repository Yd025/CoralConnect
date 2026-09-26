"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { GradeBadge } from "@/components/GradeBadge";
import { getCard, type ResultCard } from "@/lib/api";
import type { Grade } from "@/lib/types";

export default function CardPage() {
  const params = useParams<{ id: string }>();
  const id = String(params.id || "");
  const [card, setCard] = useState<ResultCard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stop = false;
    getCard(id)
      .then((data) => {
        if (!stop) setCard(data.card);
      })
      .catch((err: Error) => {
        if (!stop) setError(err.message);
      });
    return () => {
      stop = true;
    };
  }, [id]);

  return (
    <main className="phone">
      <div className="topbar">
        <a className="brand" href="/">CoralConnect</a>
      </div>
      <p className="eyebrow">{card?.kind === "collaborate" ? "Pair result" : "Competition result"}</p>
      {!card ? <h1>{error || "Loading this result…"}</h1> : null}
      {card ? (
        <section className="panel stack share-card">
          <h1>{card.names.join(" and ")}</h1>
          <p>{card.challenge}</p>
          <div className="code-block">
            <GradeBadge grade={(card.grade || null) as Grade | null} />
            <strong>{card.score}</strong>
          </div>
          <p className="muted">{card.detail}</p>
          <p className="muted">The prompt judge scored this. A higher score means less wasted model work.</p>
          <p className="link-line">{typeof window !== "undefined" ? window.location.href : ""}</p>
        </section>
      ) : null}
    </main>
  );
}
