"use client";

import { AnimatedBackground } from "@/components/AnimatedBackground";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

const CODE_LIMIT = 6;

function sanitizeCode(value: string) {
  return value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, CODE_LIMIT);
}

export default function HomePage() {
  const router = useRouter();
  const [code, setCode] = useState("");

  function join(event: FormEvent) {
    event.preventDefault();
    const next = sanitizeCode(code);
    if (!next) return;
    router.push(`/play/${next}`);
  }

  return (
    <main className="landing home">
      <AnimatedBackground />
      <div className="shell landing-ui">
        <div className="landing-stage">
          <header className="landing-top">
            <a className="brand" href="/">
              <svg className="brand-mark" viewBox="0 0 28 28" aria-hidden="true">
                <path d="M14 3 L16.2 11.2 L14 9.4 L11.8 11.2 Z" fill="currentColor" />
                <path d="M6 8 L9.2 13.2 L8 12 L6.6 14.2 Z" fill="currentColor" />
                <path d="M22 8 L18.8 13.2 L20 12 L21.4 14.2 Z" fill="currentColor" />
                <path d="M14 10.5 V24" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
              </svg>
              CoralConnect
            </a>
            <div className="landing-tools">
              <span>HackGT booth</span>
              <a className="btn-ghost" href="/admin">Host</a>
            </div>
          </header>

          <section className="hero" aria-labelledby="hero-title">
            <p className="hero-kicker"><i />A Marina’s Mission</p>
            <h1 id="hero-title">The hidden cost.</h1>
            <p className="lede">
              Leave the file out and the model searches. That search is the cost the reef shows.
            </p>
            <div className="choice-grid">
              <form id="join" className="panel stack choice" onSubmit={join}>
                <p className="eyebrow">Compete</p>
                <h2>You have a room code</h2>
                <p className="muted">Up to 10 people. You prompt on your own phone. The laptop keeps the shared reef.</p>
                <label htmlFor="game-code">
                  Room code
                  <input
                    id="game-code"
                    value={code}
                    onChange={(event) => setCode(sanitizeCode(event.target.value))}
                    maxLength={CODE_LIMIT}
                    autoCapitalize="characters"
                    autoComplete="off"
                    spellCheck={false}
                    placeholder="CODE"
                  />
                </label>
                <button className="btn" type="submit" disabled={!code}>Join this compete room</button>
              </form>
              <div className="panel stack choice">
                <p className="eyebrow">Together</p>
                <h2>Work with a partner</h2>
                <p className="muted">Two questions, then someone who is already waiting. You share one prompt, and you can play more than once.</p>
                <div className="partner-match">
                  <p><strong>You</strong><span>On your phone</span></p>
                  <p><strong>A partner</strong><span>Already waiting</span></p>
                </div>
                <a className="btn btn-warm" href="/collaborate">Work with a partner</a>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
