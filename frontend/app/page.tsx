"use client";

import { AnimatedBackground, ReefFish } from "@/components/AnimatedBackground";
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
    <main className="landing">
      <AnimatedBackground />
      <div className="shell landing-ui">
        <header className="topbar">
          <a className="brand" href="/">CoralConnect</a>
          <nav aria-label="Site">
            <a className="btn-ghost" href="/admin">Admin</a>
          </nav>
        </header>

        <section className="hero" aria-labelledby="hero-title">
          <div>
            <p className="eyebrow">HackGT · A Marina’s Mission</p>
            <h1 id="hero-title">A thin prompt makes the model search. That lookup is the carbon cost.</h1>
            <p className="lede">
              CoralConnect is a HackGT booth game. Include the source in the prompt and the model does no extra search.
              The shared reef shows what that lookup costs.
            </p>
            <div className="actions">
              <a className="btn" href="#join">Join with a code</a>
            </div>
          </div>
          <div className="hero-art" aria-hidden="true">
            <svg className="hero-glow" viewBox="0 0 460 340">
              <defs>
                <linearGradient id="hero-water" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#127a93" />
                  <stop offset="55%" stopColor="#0b4c5c" />
                  <stop offset="100%" stopColor="#042630" />
                </linearGradient>
                <linearGradient id="hero-sand" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0" stopColor="#e7c98a" />
                  <stop offset="1" stopColor="#8d6840" />
                </linearGradient>
                <radialGradient id="hero-pool" cx="50%" cy="62%" r="46%">
                  <stop offset="0%" stopColor="#3ddec8" stopOpacity="0.45" />
                  <stop offset="100%" stopColor="#3ddec8" stopOpacity="0" />
                </radialGradient>
              </defs>
              <rect width="460" height="340" rx="28" fill="url(#hero-water)" />
              <polygon points="40,0 78,0 110,180 20,180" fill="#e7f6f2" opacity="0.08" />
              <polygon points="280,0 320,0 300,200 230,200" fill="#f0d7a4" opacity="0.06" />
              <ellipse cx="230" cy="230" rx="160" ry="70" fill="url(#hero-pool)" />
              <path d="M18 250 C90 220 150 276 230 246 C310 214 370 270 446 236 L446 322 L18 322 Z" fill="url(#hero-sand)" />
              <g className="reef-sway" style={{ animationDuration: "7s" }}>
                <path d="M78 268 C70 210 46 176 38 128" fill="none" stroke="#ff6b57" strokeWidth="12" strokeLinecap="round" />
                <path d="M86 250 C70 200 84 160 72 124" fill="none" stroke="#ff8d7a" strokeWidth="8" strokeLinecap="round" />
                <path d="M92 240 C114 196 108 158 126 122" fill="none" stroke="#ff6b57" strokeWidth="7" strokeLinecap="round" />
                <circle cx="38" cy="122" r="8" fill="#ffd0c8" />
                <circle cx="72" cy="118" r="6" fill="#ffe08a" />
                <circle cx="126" cy="116" r="7" fill="#ffd0c8" />
              </g>
              <g className="reef-sway" style={{ animationDuration: "8s", animationDelay: "-2s" }}>
                <path d="M168 274 C168 210 214 168 236 196 C258 160 304 196 292 274 Z" fill="#3ddec8" />
                <path d="M196 250 C204 210 228 188 236 206" fill="none" stroke="#e7f6f2" strokeWidth="1.6" opacity="0.4" />
              </g>
              <ellipse cx="250" cy="252" rx="36" ry="20" fill="#f0d7a4" />
              <path d="M224 252 C232 242 242 258 252 246 C262 258 272 242 278 252" fill="none" stroke="#8d6840" strokeWidth="2" strokeLinecap="round" />
              <g className="reef-sway" style={{ animationDuration: "6s", animationDelay: "-1.5s" }}>
                <path d="M330 270 C324 230 314 206 318 176" fill="none" stroke="#ff6b57" strokeWidth="9" strokeLinecap="round" />
                <path d="M346 268 C356 224 372 198 366 168" fill="none" stroke="#ffd166" strokeWidth="8" strokeLinecap="round" />
                <ellipse cx="318" cy="170" rx="7" ry="10" fill="#ffb15a" />
                <ellipse cx="366" cy="162" rx="6" ry="9" fill="#ffe08a" />
                <path d="M390 268 C384 232 372 214 364 196" fill="none" stroke="#3ddec8" strokeWidth="3" strokeLinecap="round" />
                <path d="M400 266 C404 228 418 206 428 184" fill="none" stroke="#8ee89a" strokeWidth="3" strokeLinecap="round" />
                <circle cx="364" cy="190" r="5" fill="#ff8fa3" />
                <circle cx="428" cy="178" r="4" fill="#ffd166" />
              </g>
              <g transform="translate(188 86) scale(0.62)" style={{ color: "var(--sand)" }}>
                <ReefFish variant="tang" />
              </g>
              <g transform="translate(400 64) scale(-0.34, 0.34)" style={{ color: "var(--teal)" }}>
                <ReefFish variant="damsel" />
              </g>
              <circle cx="300" cy="64" r="6" fill="none" stroke="#f0d7a4" strokeWidth="1.5" />
              <circle cx="326" cy="92" r="3.5" fill="none" stroke="#3ddec8" strokeWidth="1.3" />
              <circle cx="286" cy="98" r="2.5" fill="none" stroke="#e7f6f2" strokeWidth="1.2" />
            </svg>
          </div>
        </section>

        <section className="join" id="join" aria-labelledby="join-title">
          <div>
            <p className="eyebrow">On this phone</p>
            <h2 id="join-title">Enter the code from the booth</h2>
            <p className="muted">
              The laptop at the table shows a short code. Join here and this phone becomes your controller.
            </p>
          </div>
          <form className="panel stack" onSubmit={join}>
            <label htmlFor="game-code">Game code</label>
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
            <button className="btn" type="submit" disabled={!code}>Join on this phone</button>
          </form>
        </section>

        <section className="explain" aria-labelledby="explain-title">
          <h2 id="explain-title">How the booth works</h2>
          <ol className="steps">
            <li className="panel">
              <p className="eyebrow">01</p>
              <h3>Join the reef</h3>
              <p className="muted">Use the code on the laptop. Your phone is the controller. The laptop keeps the shared reef.</p>
            </li>
            <li className="panel">
              <p className="eyebrow">02</p>
              <h3>Put the source in the prompt</h3>
              <p className="muted">The challenge already has the file. Include it so the model does no extra web search.</p>
            </li>
            <li className="panel">
              <p className="eyebrow">03</p>
              <h3>Watch the cost on the reef</h3>
              <p className="muted">A thin prompt makes the model look the answer up. That lookup clouds the water. An adequate prompt leaves the reef alive.</p>
            </li>
          </ol>
        </section>
      </div>
    </main>
  );
}
