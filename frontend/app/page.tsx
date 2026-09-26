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
          <p className="eyebrow">HackGT · A Marina’s Mission</p>
          <h1 id="hero-title">The hidden cost</h1>
          <p className="hero-script">is the lookup.</p>
          <p className="lede">
            CoralConnect is a HackGT booth game. A thin prompt makes the model search the web, and that lookup is the carbon cost.
            Include the source, and the shared reef shows the difference.
          </p>
          <div className="actions">
            <a className="btn btn-warm" href="#join">Join with a code</a>
            <a className="btn-ghost" href="#explain">How the booth works</a>
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

        <section className="explain" id="explain" aria-labelledby="explain-title">
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
