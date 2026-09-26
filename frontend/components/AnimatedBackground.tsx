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
  { id: "f1", kind: "tang", size: 28, top: "16%", duration: 34, delay: -6, depth: 0.15, fade: 0.28, reverse: false, color: "#04141c", bob: 6.2 },
  { id: "f2", kind: "damsel", size: 18, top: "24%", duration: 22, delay: -12, depth: 0.42, fade: 0.4, reverse: true, color: "#06202a", bob: 5 },
  { id: "f3", kind: "butterfly", size: 22, top: "34%", duration: 27, delay: -3, depth: 0.28, fade: 0.32, reverse: false, color: "#071820", bob: 5.6 },
  { id: "f4", kind: "tang", size: 46, top: "48%", duration: 19, delay: -8, depth: 0.85, fade: 0.55, reverse: true, color: "#031016", bob: 4.2 },
  { id: "f5", kind: "damsel", size: 16, top: "12%", duration: 16, delay: -1, depth: 0.62, fade: 0.45, reverse: false, color: "#0a2430", bob: 4.8 },
  { id: "f6", kind: "butterfly", size: 14, top: "62%", duration: 31, delay: -15, depth: 0.22, fade: 0.25, reverse: true, color: "#04141c", bob: 6 },
  { id: "f7", kind: "damsel", size: 34, top: "72%", duration: 24, delay: -9, depth: 0.5, fade: 0.38, reverse: false, color: "#052028", bob: 5.1 },
  { id: "b1", kind: "bubble", size: 7, top: "30%", duration: 20, delay: -4, depth: 0.7, fade: 0.35, reverse: false, color: "#e7f6f2", bob: 6 },
  { id: "b2", kind: "bubble", size: 5, top: "46%", duration: 15, delay: -8, depth: 0.35, fade: 0.28, reverse: true, color: "#d7f3ee", bob: 5 },
  { id: "b3", kind: "bubble", size: 9, top: "18%", duration: 26, delay: -14, depth: 0.2, fade: 0.22, reverse: false, color: "#f4fff9", bob: 7 },
];

function isControl(target: EventTarget | null) {
  return target instanceof Element && Boolean(target.closest("a, button, input, textarea, select, label"));
}

export function ReefFish({ variant }: { variant: Exclude<Kind, "bubble"> }) {
  if (variant === "butterfly") {
    return (
      <g fill="currentColor">
        <path d="M150 50 C168 34 184 30 196 26 C176 48 174 56 174 50 C174 44 176 56 196 74 C184 66 166 58 150 52 Z" />
        <path d="M28 50 C36 34 70 28 108 32 C140 36 158 44 162 50 C158 58 140 68 108 70 C70 74 36 66 28 50 Z" />
      </g>
    );
  }
  if (variant === "damsel") {
    return (
      <g fill="currentColor">
        <path d="M132 50 L186 34 L160 50 L186 66 Z" />
        <path d="M26 50 C40 38 78 36 128 44 C146 47 156 50 158 50 C156 53 146 56 128 58 C78 64 40 62 26 50 Z" />
      </g>
    );
  }
  return (
    <g fill="currentColor">
      <path d="M138 48 C158 32 176 26 192 22 C172 46 170 54 170 50 C170 46 172 56 192 78 C176 68 156 58 138 52 Z" />
      <path d="M36 50 C46 32 78 24 112 28 C140 32 156 42 160 50 C156 60 140 72 112 74 C78 78 46 68 36 50 Z" />
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
  const height = kind === "butterfly" ? size * 0.5 : kind === "damsel" ? size * 0.4 : size * 0.48;
  return (
    <svg className="drifter-fish" width={size} height={height} viewBox="0 0 200 100" style={{ animationDuration: `${bob}s` }}>
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
