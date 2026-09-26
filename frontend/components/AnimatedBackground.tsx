"use client";

import { useEffect, useRef, useState } from "react";

type Kind = "tang" | "butterfly" | "damsel" | "bubble";

type Drifter = {
  id: string;
  kind: Kind;
  size: number;
  top: string;
  duration: number;
  delay: number;
  depth: number;
  fade: number;
  reverse: boolean;
  color: string;
  bob: number;
};

type Ripple = { id: number; x: number; y: number };

const DRIFTERS: Drifter[] = [
  { id: "tang-near", kind: "tang", size: 118, top: "22%", duration: 32, delay: -8, depth: 0.72, fade: 0.92, reverse: false, color: "var(--sand)", bob: 3.4 },
  { id: "butterfly-mid", kind: "butterfly", size: 86, top: "38%", duration: 26, delay: -14, depth: 0.48, fade: 0.84, reverse: true, color: "var(--coral)", bob: 4.1 },
  { id: "damsel-fast", kind: "damsel", size: 64, top: "54%", duration: 17, delay: -3, depth: 1.05, fade: 0.95, reverse: false, color: "var(--teal)", bob: 2.6 },
  { id: "tang-far", kind: "tang", size: 48, top: "14%", duration: 38, delay: -20, depth: 0.22, fade: 0.45, reverse: true, color: "var(--warn)", bob: 4.8 },
  { id: "damsel-low", kind: "damsel", size: 54, top: "68%", duration: 22, delay: -11, depth: 0.58, fade: 0.78, reverse: true, color: "var(--good)", bob: 3.1 },
  { id: "butterfly-deep", kind: "butterfly", size: 42, top: "76%", duration: 29, delay: -5, depth: 0.3, fade: 0.5, reverse: false, color: "var(--coral)", bob: 3.8 },
  { id: "bubble-a", kind: "bubble", size: 18, top: "30%", duration: 19, delay: -6, depth: 0.9, fade: 0.7, reverse: false, color: "var(--sand)", bob: 5 },
  { id: "bubble-b", kind: "bubble", size: 12, top: "48%", duration: 14, delay: -9, depth: 0.4, fade: 0.55, reverse: true, color: "var(--teal)", bob: 4.4 },
  { id: "bubble-c", kind: "bubble", size: 22, top: "18%", duration: 24, delay: -16, depth: 0.26, fade: 0.4, reverse: false, color: "var(--ink)", bob: 5.5 },
];

function isControl(target: EventTarget | null) {
  return target instanceof Element && Boolean(target.closest("a, button, input, textarea, select, label"));
}

export function ReefFish({ variant }: { variant: Exclude<Kind, "bubble"> }) {
  if (variant === "butterfly") {
    return (
      <g>
        <path d="M132 62 C154 40 176 28 190 20 C170 52 168 66 168 70 C168 74 170 90 190 120 C176 110 154 96 132 78 Z" fill="currentColor" />
        <path d="M70 18 C92 0 128 2 146 24 C122 14 92 16 70 18 Z" fill="currentColor" />
        <path d="M74 112 C98 136 132 132 146 108 C120 118 94 120 74 112 Z" fill="currentColor" />
        <path d="M36 66 L16 58 L16 74 Z" fill="currentColor" />
        <ellipse cx="86" cy="66" rx="50" ry="46" fill="currentColor" />
        <ellipse cx="86" cy="66" rx="50" ry="46" fill="none" stroke="#042630" strokeWidth="3" opacity="0.35" />
        <path d="M52 28 C66 66 58 102 42 118" fill="none" stroke="#042630" strokeWidth="16" strokeLinecap="round" />
        <path d="M108 24 C122 66 112 108 96 124" fill="none" stroke="#042630" strokeWidth="14" strokeLinecap="round" />
        <path d="M78 70 C98 62 110 80 92 92 C84 82 78 76 78 70 Z" fill="#042630" opacity="0.18" />
        <circle cx="58" cy="58" r="11" fill="#f4fff9" />
        <circle cx="61" cy="58" r="6" fill="#042630" />
        <circle cx="59" cy="55.5" r="2.1" fill="#fff" />
      </g>
    );
  }
  if (variant === "damsel") {
    return (
      <g>
        <path d="M132 64 L186 30 L158 66 L186 102 Z" fill="currentColor" />
        <path d="M158 66 L132 64 L132 70 Z" fill="#042630" opacity="0.35" />
        <path d="M48 36 C72 8 124 12 150 40 C118 24 74 24 48 36 Z" fill="currentColor" />
        <path d="M58 96 C86 122 132 118 152 92 C120 104 82 106 58 96 Z" fill="currentColor" />
        <path d="M28 66 C40 46 78 40 128 48 C150 52 158 62 160 66 C158 70 150 80 128 84 C78 92 40 86 28 66 Z" fill="currentColor" />
        <path d="M28 66 C40 46 78 40 128 48 C150 52 158 62 160 66 C158 70 150 80 128 84 C78 92 40 86 28 66 Z" fill="none" stroke="#042630" strokeWidth="3" opacity="0.35" />
        <ellipse cx="124" cy="60" rx="16" ry="18" fill="#042630" opacity="0.82" />
        <path d="M72 64 C90 56 102 72 84 82 C76 74 72 68 72 64 Z" fill="#042630" opacity="0.2" />
        <path d="M40 52 C62 46 84 52 80 60 C60 58 42 58 40 52 Z" fill="#fff" opacity="0.2" />
        <circle cx="52" cy="58" r="9" fill="#f4fff9" />
        <circle cx="55" cy="58" r="4.6" fill="#042630" />
        <circle cx="53.2" cy="56" r="1.7" fill="#fff" />
      </g>
    );
  }
  return (
    <g>
      <path d="M138 58 C160 34 182 20 196 12 C176 46 174 62 174 66 C174 70 176 88 196 118 C182 106 160 92 138 76 Z" fill="currentColor" />
      <path d="M62 22 C84 0 126 2 150 28 C122 16 86 18 62 22 Z" fill="currentColor" />
      <path d="M68 108 C92 134 132 130 152 104 C124 116 90 118 68 108 Z" fill="currentColor" />
      <path d="M30 66 C38 54 50 50 62 54 C50 62 50 72 62 80 C50 84 38 78 30 66 Z" fill="currentColor" />
      <ellipse cx="92" cy="66" rx="56" ry="42" fill="currentColor" />
      <ellipse cx="92" cy="66" rx="56" ry="42" fill="none" stroke="#042630" strokeWidth="3" opacity="0.35" />
      <path d="M126 86 L112 124 L136 98 Z" fill="#f4fff9" stroke="#042630" strokeWidth="2" />
      <path d="M78 70 C100 60 114 82 90 96 C80 84 78 76 78 70 Z" fill="#042630" opacity="0.2" />
      <path d="M52 42 C78 34 104 42 100 54 C76 52 54 50 52 42 Z" fill="#fff" opacity="0.22" />
      <path d="M70 36 C66 56 68 78 78 96" fill="none" stroke="#042630" strokeWidth="3" strokeLinecap="round" opacity="0.22" />
      <circle cx="58" cy="58" r="11" fill="#f4fff9" />
      <circle cx="61" cy="58" r="5.5" fill="#042630" />
      <circle cx="59" cy="55.4" r="2" fill="#fff" />
    </g>
  );
}

function Shape({ kind, size, bob }: { kind: Kind; size: number; bob: number }) {
  if (kind === "bubble") {
    return (
      <svg width={size} height={size} viewBox="0 0 32 32" style={{ animationDuration: `${bob}s` }}>
        <circle cx="16" cy="16" r="10" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <path d="M11 12 C13 9 16 9 17 12" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
      </svg>
    );
  }
  const height = kind === "butterfly" ? size * 0.68 : kind === "damsel" ? size * 0.58 : size * 0.66;
  return (
    <svg className="drifter-fish" width={size} height={height} viewBox="0 0 200 136" style={{ animationDuration: `${bob}s` }}>
      <ReefFish variant={kind} />
    </svg>
  );
}

function ReefBed() {
  return (
    <div className="ambient-parallax ambient-reef" style={{ ["--depth" as string]: 0.14, ["--layer" as string]: 1 }}>
      <svg className="ambient-reef-art" viewBox="0 0 1200 460" preserveAspectRatio="xMidYMax slice">
        <defs>
          <linearGradient id="ambient-sand" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#e7c98a" />
            <stop offset="1" stopColor="#8d6840" />
          </linearGradient>
        </defs>
        <path d="M0 292 C140 250 260 320 420 286 C620 244 760 330 960 286 C1080 264 1140 300 1200 276 L1200 460 L0 460 Z" fill="url(#ambient-sand)" />
        <ellipse cx="180" cy="360" rx="90" ry="16" fill="#6d4e2e" opacity="0.28" />
        <ellipse cx="740" cy="372" rx="130" ry="18" fill="#6d4e2e" opacity="0.25" />
        <ellipse cx="1040" cy="348" rx="70" ry="12" fill="#6d4e2e" opacity="0.22" />

        <g className="reef-sway" style={{ animationDuration: "7.5s" }}>
          <path d="M90 340 C78 270 48 230 40 170" fill="none" stroke="var(--coral)" strokeWidth="16" strokeLinecap="round" />
          <path d="M96 300 C70 250 86 190 70 150" fill="none" stroke="var(--coral)" strokeWidth="11" strokeLinecap="round" />
          <path d="M100 280 C130 230 118 180 142 142" fill="none" stroke="#ff8d7a" strokeWidth="10" strokeLinecap="round" />
          <circle cx="40" cy="164" r="12" fill="#ffd0c8" />
          <circle cx="70" cy="144" r="9" fill="#ffd0c8" />
          <circle cx="142" cy="136" r="10" fill="#ffd0c8" />
        </g>

        <g className="reef-sway" style={{ animationDuration: "8.4s", animationDelay: "-2s" }}>
          <path d="M250 348 C250 250 330 190 360 230 C390 180 470 240 450 348 Z" fill="var(--teal)" opacity="0.9" />
          <path d="M300 330 C310 260 350 230 360 250" fill="none" stroke="#e7f6f2" strokeWidth="2" opacity="0.35" />
          <path d="M360 320 C372 250 410 220 420 260" fill="none" stroke="#e7f6f2" strokeWidth="2" opacity="0.3" />
          <path d="M250 348 C270 300 250 250 236 210" fill="none" stroke="var(--good)" strokeWidth="8" strokeLinecap="round" />
        </g>

        <g>
          <ellipse cx="560" cy="318" rx="62" ry="36" fill="var(--sand)" />
          <path d="M512 318 C524 304 536 330 548 312 C560 330 572 304 584 318 C596 304 608 328 610 318" fill="none" stroke="#8d6840" strokeWidth="3" strokeLinecap="round" />
          <path d="M518 332 C534 320 548 340 562 326 C576 342 590 320 604 332" fill="none" stroke="#8d6840" strokeWidth="3" strokeLinecap="round" />
          <ellipse cx="520" cy="346" rx="28" ry="12" fill="#c9a36a" />
        </g>

        <g className="reef-sway" style={{ animationDuration: "6.2s", animationDelay: "-1s" }}>
          <path d="M690 350 C686 300 670 270 676 230" fill="none" stroke="var(--coral)" strokeWidth="14" strokeLinecap="round" />
          <path d="M708 348 C720 290 742 250 734 210" fill="none" stroke="var(--warn)" strokeWidth="12" strokeLinecap="round" />
          <path d="M724 346 C744 300 770 270 786 228" fill="none" stroke="var(--coral)" strokeWidth="10" strokeLinecap="round" />
          <ellipse cx="676" cy="224" rx="12" ry="16" fill="#ffb15a" />
          <ellipse cx="734" cy="204" rx="11" ry="15" fill="#ffe08a" />
          <ellipse cx="786" cy="222" rx="10" ry="14" fill="#ff8d7a" />
        </g>

        <g className="reef-sway" style={{ animationDuration: "5.4s", animationDelay: "-3s" }}>
          <path d="M860 340 C848 300 832 280 820 250" fill="none" stroke="var(--teal)" strokeWidth="4" strokeLinecap="round" />
          <path d="M868 342 C860 292 878 250 868 214" fill="none" stroke="var(--teal)" strokeWidth="4" strokeLinecap="round" />
          <path d="M878 338 C892 290 910 260 928 228" fill="none" stroke="var(--good)" strokeWidth="4" strokeLinecap="round" />
          <path d="M850 344 C844 310 824 290 808 268" fill="none" stroke="var(--sand)" strokeWidth="3" strokeLinecap="round" />
          <circle cx="820" cy="244" r="7" fill="#ffb4a2" />
          <circle cx="868" cy="208" r="8" fill="#ff8fa3" />
          <circle cx="928" cy="222" r="6" fill="#ffd166" />
          <ellipse cx="868" cy="348" rx="36" ry="10" fill="#1d6a62" />
        </g>

        <g className="reef-sway" style={{ animationDuration: "7s", animationDelay: "-4s" }}>
          <path d="M1020 330 C1004 260 980 210 990 150" fill="none" stroke="var(--coral)" strokeWidth="13" strokeLinecap="round" />
          <path d="M1030 310 C1056 250 1044 190 1068 150" fill="none" stroke="#ff8d7a" strokeWidth="9" strokeLinecap="round" />
          <path d="M1040 300 C1076 240 1104 200 1116 156" fill="none" stroke="var(--warn)" strokeWidth="8" strokeLinecap="round" />
          <circle cx="990" cy="144" r="9" fill="#ffd0c8" />
          <circle cx="1068" cy="144" r="8" fill="#ffe08a" />
          <circle cx="1116" cy="150" r="8" fill="#ffd0c8" />
        </g>

        <g className="reef-sway" style={{ animationDuration: "6.8s", animationDelay: "-2.5s" }}>
          <path d="M160 360 C150 320 130 300 118 270" fill="none" stroke="#1d6a62" strokeWidth="3" strokeLinecap="round" />
          <path d="M172 358 C176 318 196 290 206 258" fill="none" stroke="#1d6a62" strokeWidth="3" strokeLinecap="round" />
          <path d="M400 360 C392 324 376 300 368 274" fill="none" stroke="#14584f" strokeWidth="3" strokeLinecap="round" />
          <path d="M960 340 C952 300 940 280 930 252" fill="none" stroke="#14584f" strokeWidth="3" strokeLinecap="round" />
        </g>
      </svg>
    </div>
  );
}

export function AnimatedBackground() {
  const rootRef = useRef<HTMLDivElement>(null);
  const ids = useRef(0);
  const [ripples, setRipples] = useState<Ripple[]>([]);

  useEffect(() => {
    const node = rootRef.current;
    if (!node) return;

    const point = { x: 0, y: 0 };
    let frame = 0;
    let lastRipple = 0;
    const timers = new Set<number>();

    const flush = () => {
      frame = 0;
      node.style.setProperty("--px", point.x.toFixed(4));
      node.style.setProperty("--py", point.y.toFixed(4));
    };

    const onMove = (event: PointerEvent) => {
      point.x = (event.clientX / window.innerWidth - 0.5) * 2;
      point.y = (event.clientY / window.innerHeight - 0.5) * 2;
      if (frame === 0) frame = requestAnimationFrame(flush);
    };

    const spawn = (event: Event) => {
      if (isControl(event.target)) return;
      if (!("clientX" in event) || !("clientY" in event)) return;
      const pointer = event as PointerEvent;
      const now = performance.now();
      if (now - lastRipple < 50) return;
      lastRipple = now;
      const id = ++ids.current;
      const ripple = { id, x: pointer.clientX, y: pointer.clientY };
      setRipples((items) => {
        const next = [...items, ripple];
        return next.length > 10 ? next.slice(next.length - 10) : next;
      });
      const timer = window.setTimeout(() => {
        timers.delete(timer);
        setRipples((items) => items.filter((item) => item.id !== id));
      }, 3300);
      timers.add(timer);
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerdown", spawn, true);
    window.addEventListener("click", spawn, true);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerdown", spawn, true);
      window.removeEventListener("click", spawn, true);
      if (frame) cancelAnimationFrame(frame);
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, []);

  return (
    <>
    <div className="ambient" ref={rootRef} aria-hidden="true">
      <svg className="ambient-rays" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMin slice">
        <polygon points="140,0 210,0 280,520 120,520" fill="#e7f6f2" opacity="0.07" />
        <polygon points="560,0 640,0 700,560 480,560" fill="#e7f6f2" opacity="0.06" />
        <polygon points="960,0 1030,0 960,420 860,420" fill="#f0d7a4" opacity="0.05" />
      </svg>
      <ReefBed />
      {DRIFTERS.map((item) => (
        <div
          key={item.id}
          className="ambient-parallax"
          style={{
            top: item.top,
            ["--depth" as string]: item.depth,
            ["--layer" as string]: Math.round(item.depth * 10),
          }}
        >
          <span
            className={item.reverse ? "ambient-track is-reverse" : "ambient-track"}
            style={{
              color: item.color,
              animationDuration: `${item.duration}s`,
              animationDelay: `${item.delay}s`,
              ["--fade" as string]: item.fade,
            }}
          >
            <Shape kind={item.kind} size={item.size} bob={item.bob} />
          </span>
        </div>
      ))}
    </div>
    <div className="ambient-ripples" aria-hidden="true">
      {ripples.map((ripple) => (
        <span key={ripple.id} className="ambient-ripple" style={{ left: ripple.x, top: ripple.y }} />
      ))}
    </div>
    </>
  );
}
