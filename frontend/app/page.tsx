"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export default function HomePage() {
  const router = useRouter();
  const [code, setCode] = useState("");

  function join(event: FormEvent) {
    event.preventDefault();
    const next = code.trim().toUpperCase();
    if (next) router.push(`/play/${next}`);
  }

  return (
    <main className="shell">
      <div className="topbar">
        <span className="brand">CoralConnect</span>
        <a className="btn-ghost" href="/admin">Admin</a>
      </div>
      <section className="hero">
        <div>
          <p className="eyebrow">HackGT · A Marina’s Mission</p>
          <h1>Give the model the source, or it goes looking.</h1>
          <p className="lede">
            A vague prompt sends the model to the web. That lookup is the waste. Include the source in the message
            and the shared reef stays alive.
          </p>
          <div className="actions">
            <a className="btn" href="/admin">Open the booth console</a>
          </div>
        </div>
        <form className="panel stack" onSubmit={join}>
          <p className="eyebrow">I have a code</p>
          <label>
            Game code
            <input
              value={code}
              onChange={(event) => setCode(event.target.value.toUpperCase())}
              maxLength={6}
              autoCapitalize="characters"
            />
          </label>
          <button className="btn" type="submit">Join on this phone</button>
        </form>
      </section>
    </main>
  );
}
