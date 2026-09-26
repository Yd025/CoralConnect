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
                  <stop offset="0%" stopColor="#0c4a56" />
                  <stop offset="58%" stopColor="#06343c" />
                  <stop offset="100%" stopColor="#03161c" />
                </linearGradient>
                <linearGradient id="hero-sand" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0" stopColor="#8d7350" />
                  <stop offset="1" stopColor="#3e3428" />
                </linearGradient>
                <radialGradient id="hero-pool" cx="50%" cy="64%" r="42%">
                  <stop offset="0%" stopColor="#3ddec8" stopOpacity="0.22" />
                  <stop offset="100%" stopColor="#3ddec8" stopOpacity="0" />
                </radialGradient>
              </defs>
              <rect width="460" height="340" rx="28" fill="url(#hero-water)" />
              <polygon points="48,0 70,0 96,170 28,170" fill="#e7f6f2" opacity="0.045" />
              <ellipse cx="230" cy="236" rx="150" ry="58" fill="url(#hero-pool)" />
              <path d="M16 262 C100 236 160 286 240 258 C320 230 380 284 448 250 L448 324 L16 324 Z" fill="url(#hero-sand)" />
              <g className="reef-sway" strokeLinecap="round" style={{ animationDuration: "9s" }}>
                <path d="M72 286 C66 236 48 206 42 168" fill="none" stroke="#d85a4c" strokeWidth="3.4" opacity="0.85" />
                <path d="M78 260 C64 228 70 198 60 172" fill="none" stroke="var(--coral)" strokeWidth="2" opacity="0.7" />
                <path d="M84 246 C102 214 96 186 110 162" fill="none" stroke="#c9843a" strokeWidth="1.7" opacity="0.7" />
                <path d="M58 230 C44 208 48 188 38 170" fill="none" stroke="#d85a4c" strokeWidth="1.3" opacity="0.6" />
              </g>
              <g className="reef-sway" style={{ animationDuration: "11s", animationDelay: "-2s" }}>
                <path d="M168 292 C166 236 210 198 236 214 C262 190 304 228 292 292 Z" fill="#3ddec8" opacity="0.32" />
                <path d="M186 280 C192 240 214 220 230 232" fill="none" stroke="#9ec4bc" strokeWidth="1" opacity="0.45" />
                <path d="M214 284 C224 236 256 214 274 236" fill="none" stroke="#9ec4bc" strokeWidth="1" opacity="0.35" />
              </g>
              <ellipse cx="248" cy="268" rx="30" ry="14" fill="#6e5a40" />
              <path d="M226 266 C236 258 246 274 256 260 C266 274 276 258 284 266" fill="none" stroke="#3e3428" strokeWidth="1.1" />
              <g className="reef-sway" strokeLinecap="round" style={{ animationDuration: "8.5s", animationDelay: "-1.4s" }}>
                <path d="M334 284 C330 248 322 228 326 204" fill="none" stroke="var(--coral)" strokeWidth="2.6" opacity="0.8" />
                <path d="M348 282 C356 244 368 224 364 200" fill="none" stroke="#c9843a" strokeWidth="1.8" opacity="0.7" />
                <path d="M360 280 C372 246 386 228 398 208" fill="none" stroke="#d85a4c" strokeWidth="1.4" opacity="0.65" />
                <path d="M390 286 C384 252 374 236 368 218" fill="none" stroke="var(--teal)" strokeWidth="1.2" opacity="0.5" />
                <path d="M402 284 C408 250 420 232 430 214" fill="none" stroke="#7dbea8" strokeWidth="1.1" opacity="0.45" />
              </g>
              <g transform="translate(214 108) scale(0.5)" style={{ color: "var(--sand)" }}>
                <ReefFish variant="tang" />
              </g>
              <g transform="translate(392 86) scale(-0.3, 0.3)" style={{ color: "var(--teal)" }}>
                <ReefFish variant="damsel" />
              </g>
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
