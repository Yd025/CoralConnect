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
  { id: "tang-near", kind: "tang", size: 110, top: "22%", duration: 32, delay: -8, depth: 0.7, fade: 0.92, reverse: false, color: "var(--sand)", bob: 4.2 },
  { id: "butterfly-mid", kind: "butterfly", size: 84, top: "40%", duration: 26, delay: -14, depth: 0.46, fade: 0.88, reverse: true, color: "var(--coral)", bob: 4.8 },
  { id: "damsel-fast", kind: "damsel", size: 64, top: "58%", duration: 18, delay: -3, depth: 0.95, fade: 0.9, reverse: false, color: "var(--teal)", bob: 3.4 },
  { id: "tang-far", kind: "tang", size: 42, top: "14%", duration: 40, delay: -18, depth: 0.2, fade: 0.45, reverse: true, color: "var(--warn)", bob: 5.2 },
  { id: "damsel-low", kind: "damsel", size: 48, top: "74%", duration: 23, delay: -11, depth: 0.55, fade: 0.7, reverse: true, color: "var(--good)", bob: 4 },
  { id: "b1", kind: "bubble", size: 14, top: "30%", duration: 20, delay: -6, depth: 0.8, fade: 0.55, reverse: false, color: "var(--sand)", bob: 5.5 },
  { id: "b2", kind: "bubble", size: 9, top: "48%", duration: 15, delay: -9, depth: 0.35, fade: 0.4, reverse: true, color: "var(--ink)", bob: 5 },
];

function isControl(target: EventTarget | null) {
  return target instanceof Element && Boolean(target.closest("a, button, input, textarea, select, label"));
}

export function ReefFish({ variant }: { variant: Exclude<Kind, "bubble"> }) {
  if (variant === "butterfly") {
    return (
      <g>
        <path d="M148 48 C166 30 182 24 194 18 C174 44 172 54 172 50 C172 46 174 58 194 82 C180 72 162 60 148 52 Z" fill="currentColor" />
        <path d="M24 50 C30 42 40 40 48 44 C40 50 40 54 48 58 C40 62 30 58 24 50 Z" fill="currentColor" />
        <path d="M46 50 C52 30 78 20 108 22 C138 24 156 36 160 50 C156 64 138 78 108 78 C78 80 52 70 46 50 Z" fill="currentColor" />
        <path d="M78 24 C96 14 124 16 140 28 C118 22 94 22 78 28 Z" fill="currentColor" opacity="0.85" />
        <path d="M82 74 C102 88 130 84 144 70 C122 76 98 76 82 72 Z" fill="currentColor" opacity="0.75" />
        <path d="M62 28 C70 50 66 68 54 78" fill="none" stroke="#2a2118" strokeWidth="7" strokeLinecap="round" />
        <path d="M104 24 C114 50 108 72 94 82" fill="none" stroke="#2a2118" strokeWidth="6" strokeLinecap="round" />
        <circle cx="52" cy="44" r="6" fill="#f4fff9" />
        <circle cx="54" cy="44" r="3.2" fill="#042630" />
      </g>
    );
  }
  if (variant === "damsel") {
    return (
      <g>
        <path d="M136 46 L188 22 L162 50 L188 78 Z" fill="currentColor" />
        <path d="M30 50 C42 32 78 28 118 36 C142 40 156 46 160 50 C156 54 142 62 118 64 C78 72 42 68 30 50 Z" fill="currentColor" />
        <path d="M70 34 C92 24 118 28 136 40" fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" opacity="0.7" />
        <ellipse cx="122" cy="46" rx="9" ry="7" fill="#042630" opacity="0.55" />
        <circle cx="50" cy="46" r="5.5" fill="#f4fff9" />
        <circle cx="52" cy="46" r="2.8" fill="#042630" />
      </g>
    );
  }
  return (
    <g>
      <path d="M140 44 C162 24 180 14 196 8 C174 40 172 52 172 50 C172 48 174 62 196 92 C180 80 160 64 140 54 Z" fill="currentColor" />
      <path d="M70 26 C92 8 124 8 146 26 C122 18 92 18 70 28 Z" fill="currentColor" />
      <path d="M76 76 C98 96 130 92 148 74 C124 82 96 84 76 76 Z" fill="currentColor" opacity="0.85" />
      <path d="M34 50 C44 28 76 16 110 18 C140 20 158 34 162 50 C158 66 140 82 110 82 C76 84 44 72 34 50 Z" fill="currentColor" />
      <path d="M126 64 L114 86 L136 70 Z" fill="#f7f4ee" />
      <circle cx="58" cy="44" r="6" fill="#f4fff9" />
      <circle cx="60" cy="44" r="3.2" fill="#042630" />
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
  const height = kind === "butterfly" ? size * 0.62 : kind === "damsel" ? size * 0.5 : size * 0.58;
  return (
    <svg className="drifter-fish" width={size} height={height} viewBox="0 0 200 110" style={{ animationDuration: `${bob}s` }}>
      <ReefFish variant={kind} />
    </svg>
  );
}

function ReefBed() {
  return (
    <div className="ambient-parallax ambient-reef" style={{ ["--depth" as string]: 0.14, ["--layer" as string]: 1 }}>
      <svg className="ambient-reef-art" viewBox="0 0 1200 520" preserveAspectRatio="xMidYMax slice">
        <defs>
          <linearGradient id="ambient-sand" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#a48862" />
            <stop offset="1" stopColor="#4a3b2c" />
          </linearGradient>
          <linearGradient id="stag-shade" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f0a090" />
            <stop offset="40%" stopColor="#d46552" />
            <stop offset="100%" stopColor="#8d3a34" />
          </linearGradient>
          <linearGradient id="lobe-shade" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#e7b08a" />
            <stop offset="100%" stopColor="#a85a40" />
          </linearGradient>
          <linearGradient id="fan-shade" x1="0" y1="1" x2="0" y2="0">
            <stop offset="0%" stopColor="#14584f" />
            <stop offset="100%" stopColor="#3ddec8" />
          </linearGradient>
        </defs>
        <path d="M0 390 C170 340 300 420 500 372 C720 318 900 430 1200 360 L1200 520 L0 520 Z" fill="url(#ambient-sand)" />
        <path d="M-20 180 C70 220 90 360 40 520 L-20 520 Z" fill="#07141a" />
        <path d="M1220 140 C1080 220 1040 360 1140 520 L1220 520 Z" fill="#07141a" />
        <ellipse cx="180" cy="470" rx="120" ry="18" fill="#1a120e" opacity="0.35" />
        <ellipse cx="860" cy="488" rx="160" ry="20" fill="#1a120e" opacity="0.28" />

        <g className="reef-sway" style={{ animationDuration: "11s" }}>
          <path d="M48 500 C36 420 8 360 30 290 C52 360 64 420 78 500 Z" fill="url(#stag-shade)" />
          <path d="M86 510 C96 410 140 340 118 270 C150 350 148 430 132 510 Z" fill="#e0894a" />
          <path d="M130 516 C158 430 196 370 176 300 C214 380 196 450 176 516 Z" fill="url(#lobe-shade)" />
          <path d="M70 500 C64 450 48 410 56 370 C70 420 78 460 86 500 Z" fill="#f0b27a" opacity="0.85" />
        </g>

        <g className="reef-sway" style={{ animationDuration: "13s", animationDelay: "-4s" }}>
          <path d="M250 500 C240 410 210 350 236 286 C280 340 300 250 338 300 C360 360 390 430 360 500 Z" fill="url(#fan-shade)" opacity="0.72" />
          <path d="M292 490 C286 400 270 340 286 292" fill="none" stroke="#b7efe4" strokeWidth="1.2" opacity="0.35" />
          <path d="M292 490 C310 390 330 330 346 286" fill="none" stroke="#b7efe4" strokeWidth="1.2" opacity="0.28" />
          <path d="M292 490 C270 410 250 360 236 310" fill="none" stroke="#083830" strokeWidth="1.4" opacity="0.25" />
        </g>

        <g opacity="0.95">
          <ellipse cx="560" cy="455" rx="78" ry="34" fill="#6a5340" />
          <ellipse cx="560" cy="446" rx="78" ry="28" fill="#8d6d4e" />
          <path d="M500 446 C518 434 534 458 552 438 C570 458 588 432 606 446" fill="none" stroke="#4a382c" strokeWidth="1.6" />
          <path d="M508 458 C528 448 546 466 564 450 C582 466 598 446 616 456" fill="none" stroke="#4a382c" strokeWidth="1.3" />
        </g>

        <g className="reef-sway" style={{ animationDuration: "10s", animationDelay: "-2s" }}>
          <path d="M700 500 C692 440 676 400 684 350 C700 400 706 450 714 500 Z" fill="url(#stag-shade)" />
          <path d="M724 506 C736 430 770 370 754 318 C786 380 778 450 764 506 Z" fill="#e0894a" />
          <path d="M770 508 C798 440 834 390 816 336 C848 400 836 460 820 508 Z" fill="#f0b27a" />
          <path d="M748 500 C754 450 770 410 762 368 C780 420 776 460 782 500 Z" fill="#c45a42" opacity="0.8" />
        </g>

        <g className="reef-sway" style={{ animationDuration: "12s", animationDelay: "-6s" }}>
          <path d="M980 490 C960 400 930 340 956 270 C1000 330 1030 250 1074 292 C1100 360 1120 430 1060 490 Z" fill="url(#fan-shade)" opacity="0.55" />
          <path d="M1020 480 C1010 390 990 330 1004 286" fill="none" stroke="#d7fff6" strokeWidth="1" opacity="0.3" />
          <path d="M1020 480 C1044 380 1070 320 1088 278" fill="none" stroke="#d7fff6" strokeWidth="1" opacity="0.22" />
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
      <svg className="ambient-rays hero-glow" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMin slice">
        <defs>
          <linearGradient id="godray" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#e9fff8" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#e9fff8" stopOpacity="0" />
          </linearGradient>
          <radialGradient id="sunbloom" cx="78%" cy="0%" r="42%">
            <stop offset="0%" stopColor="#f4fff9" stopOpacity="0.85" />
            <stop offset="28%" stopColor="#7ee7dc" stopOpacity="0.45" />
            <stop offset="100%" stopColor="#7ee7dc" stopOpacity="0" />
          </radialGradient>
        </defs>
        <rect width="1200" height="800" fill="url(#sunbloom)" />
        <polygon points="860,0 980,0 760,800 520,800" fill="url(#godray)" />
        <polygon points="980,0 1100,0 1040,760 820,760" fill="url(#godray)" opacity="0.65" />
        <polygon points="720,0 800,0 640,680 470,680" fill="url(#godray)" opacity="0.4" />
      </svg>
      <div className="ambient-vignette" />
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
