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
  { id: "tang-near", kind: "tang", size: 96, top: "24%", duration: 36, delay: -8, depth: 0.62, fade: 0.72, reverse: false, color: "var(--sand)", bob: 4.6 },
  { id: "butterfly-mid", kind: "butterfly", size: 72, top: "40%", duration: 30, delay: -14, depth: 0.4, fade: 0.62, reverse: true, color: "var(--coral)", bob: 5.2 },
  { id: "damsel-fast", kind: "damsel", size: 58, top: "56%", duration: 22, delay: -3, depth: 0.88, fade: 0.7, reverse: false, color: "var(--teal)", bob: 3.8 },
  { id: "tang-far", kind: "tang", size: 40, top: "16%", duration: 44, delay: -20, depth: 0.18, fade: 0.32, reverse: true, color: "var(--warn)", bob: 6 },
  { id: "damsel-low", kind: "damsel", size: 46, top: "70%", duration: 27, delay: -11, depth: 0.5, fade: 0.55, reverse: true, color: "var(--good)", bob: 4.4 },
  { id: "butterfly-deep", kind: "butterfly", size: 36, top: "78%", duration: 34, delay: -5, depth: 0.24, fade: 0.34, reverse: false, color: "var(--coral)", bob: 5.4 },
  { id: "bubble-a", kind: "bubble", size: 11, top: "32%", duration: 22, delay: -6, depth: 0.7, fade: 0.4, reverse: false, color: "var(--sand)", bob: 6 },
  { id: "bubble-b", kind: "bubble", size: 8, top: "50%", duration: 18, delay: -9, depth: 0.35, fade: 0.32, reverse: true, color: "var(--teal)", bob: 5 },
  { id: "bubble-c", kind: "bubble", size: 14, top: "20%", duration: 28, delay: -16, depth: 0.2, fade: 0.22, reverse: false, color: "var(--ink)", bob: 6.5 },
];

function isControl(target: EventTarget | null) {
  return target instanceof Element && Boolean(target.closest("a, button, input, textarea, select, label"));
}

function Eye({ cx, cy }: { cx: number; cy: number }) {
  return (
    <g>
      <circle cx={cx} cy={cy} r="3.1" fill="#102028" />
      <circle cx={cx - 0.8} cy={cy - 0.8} r="0.85" fill="#f4fff9" opacity="0.75" />
    </g>
  );
}

export function ReefFish({ variant }: { variant: Exclude<Kind, "bubble"> }) {
  if (variant === "butterfly") {
    return (
      <g>
        <path d="M146 50 C162 38 176 34 186 32 C170 48 168 54 168 50 C168 46 170 52 186 68 C176 66 162 60 146 52 Z" fill="currentColor" opacity="0.8" />
        <path d="M34 50 C48 34 78 30 112 34 C136 37 150 44 154 50 C150 56 136 64 112 67 C78 71 48 66 34 50 Z" fill="currentColor" />
        <path d="M28 50 C34 46 40 46 44 50 C40 54 34 54 28 50 Z" fill="currentColor" />
        <path d="M70 36 C86 28 108 30 122 38" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" opacity="0.55" />
        <path d="M74 64 C90 72 112 70 126 62" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" opacity="0.45" />
        <path d="M58 36 C64 50 62 62 54 68" fill="none" stroke="#102028" strokeWidth="4.5" strokeLinecap="round" opacity="0.55" />
        <path d="M96 34 C104 50 100 64 90 70" fill="none" stroke="#102028" strokeWidth="3.5" strokeLinecap="round" opacity="0.4" />
        <path d="M48 54 C64 58 78 56 86 50" fill="none" stroke="#fff" strokeWidth="1" opacity="0.18" />
        <Eye cx={48} cy={46} />
      </g>
    );
  }
  if (variant === "damsel") {
    return (
      <g>
        <path d="M138 50 L176 36 L158 50 L176 64 Z" fill="currentColor" opacity="0.9" />
        <path d="M32 50 C46 38 84 36 124 42 C140 45 150 48 152 50 C150 52 140 56 124 58 C84 64 46 62 32 50 Z" fill="currentColor" />
        <path d="M70 40 C90 34 112 36 128 44" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" opacity="0.5" />
        <ellipse cx="118" cy="48" rx="7" ry="5" fill="#102028" opacity="0.55" />
        <path d="M44 46 C58 44 70 46 78 50" fill="none" stroke="#fff" strokeWidth="1" opacity="0.16" />
        <Eye cx={52} cy={47} />
      </g>
    );
  }
  return (
    <g>
      <path d="M142 48 C160 34 178 28 190 24 C172 44 170 52 170 50 C170 48 172 56 190 76 C178 70 160 60 142 52 Z" fill="currentColor" opacity="0.88" />
      <path d="M40 50 C52 32 82 26 114 30 C138 33 152 42 154 50 C152 58 138 68 114 70 C82 74 52 68 40 50 Z" fill="currentColor" />
      <path d="M78 32 C96 24 122 26 138 36" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" opacity="0.55" />
      <path d="M82 68 C102 76 126 74 140 64" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" opacity="0.4" />
      <path d="M128 58 L122 72 L134 60 Z" fill="#e7f6f2" opacity="0.55" />
      <path d="M56 44 C78 40 98 44 108 50" fill="none" stroke="#fff" strokeWidth="1.2" opacity="0.18" />
      <Eye cx={62} cy={46} />
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
      <svg className="ambient-reef-art" viewBox="0 0 1200 460" preserveAspectRatio="xMidYMax slice">
        <defs>
          <linearGradient id="ambient-sand" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#8d7350" />
            <stop offset="1" stopColor="#3e3428" />
          </linearGradient>
        </defs>
        <path d="M0 318 C160 286 280 340 460 308 C680 268 820 348 1040 304 C1140 284 1180 310 1200 296 L1200 460 L0 460 Z" fill="url(#ambient-sand)" />
        <path d="M40 360 C120 348 180 372 260 356 C340 340 400 368 480 352" fill="none" stroke="#2a241c" strokeWidth="1" opacity="0.35" />
        <ellipse cx="210" cy="372" rx="70" ry="10" fill="#241c16" opacity="0.28" />
        <ellipse cx="780" cy="384" rx="110" ry="12" fill="#241c16" opacity="0.22" />

        <g className="reef-sway" strokeLinecap="round" style={{ animationDuration: "9s" }}>
          <path d="M70 360 C62 300 40 260 34 214" fill="none" stroke="var(--coral)" strokeWidth="4.5" opacity="0.8" />
          <path d="M74 320 C58 280 66 246 54 214" fill="none" stroke="var(--coral)" strokeWidth="2.4" opacity="0.7" />
          <path d="M78 300 C96 262 88 230 102 198" fill="none" stroke="#d85a4c" strokeWidth="2.2" opacity="0.75" />
          <path d="M60 286 C44 258 50 232 38 208" fill="none" stroke="var(--coral)" strokeWidth="1.8" opacity="0.6" />
          <path d="M96 248 C112 224 106 202 118 184" fill="none" stroke="#d85a4c" strokeWidth="1.4" opacity="0.65" />
        </g>

        <g className="reef-sway" style={{ animationDuration: "11s", animationDelay: "-3s" }}>
          <path d="M250 368 C248 300 310 250 348 268 C386 246 430 292 418 368 Z" fill="var(--teal)" opacity="0.28" />
          <path d="M268 360 C272 300 310 268 332 286" fill="none" stroke="var(--teal)" strokeWidth="1.1" opacity="0.55" />
          <path d="M300 364 C308 292 348 258 366 290" fill="none" stroke="var(--teal)" strokeWidth="1.1" opacity="0.5" />
          <path d="M332 362 C346 300 390 270 408 300" fill="none" stroke="#9ec4bc" strokeWidth="1" opacity="0.4" />
          <path d="M248 360 C258 320 246 286 236 258" fill="none" stroke="#1d6a62" strokeWidth="1.6" opacity="0.55" />
        </g>

        <g opacity="0.9">
          <ellipse cx="560" cy="332" rx="54" ry="22" fill="#6e5a40" />
          <path d="M516 328 C528 320 540 336 552 322 C564 336 576 318 588 328 C598 318 606 332 608 326" fill="none" stroke="#3e3428" strokeWidth="1.2" />
          <path d="M520 338 C534 330 548 344 562 332 C576 344 588 330 602 338" fill="none" stroke="#3e3428" strokeWidth="1.1" />
          <ellipse cx="530" cy="346" rx="22" ry="7" fill="#5c4a34" opacity="0.8" />
        </g>

        <g className="reef-sway" strokeLinecap="round" style={{ animationDuration: "8.5s", animationDelay: "-2s" }}>
          <path d="M700 358 C696 318 684 292 688 262" fill="none" stroke="var(--coral)" strokeWidth="3.2" opacity="0.75" />
          <path d="M714 356 C722 312 738 286 732 256" fill="none" stroke="#c9843a" strokeWidth="2.4" opacity="0.7" />
          <path d="M728 354 C742 316 760 294 772 266" fill="none" stroke="var(--coral)" strokeWidth="2" opacity="0.65" />
          <path d="M708 300 C698 284 702 270 694 256" fill="none" stroke="#d85a4c" strokeWidth="1.3" opacity="0.6" />
        </g>

        <g className="reef-sway" strokeLinecap="round" style={{ animationDuration: "10s", animationDelay: "-4s" }}>
          <path d="M860 352 C852 318 838 300 828 276" fill="none" stroke="var(--teal)" strokeWidth="1.5" opacity="0.55" />
          <path d="M870 354 C866 314 880 286 872 258" fill="none" stroke="var(--teal)" strokeWidth="1.5" opacity="0.6" />
          <path d="M882 350 C894 314 908 292 922 268" fill="none" stroke="#7dbea8" strokeWidth="1.4" opacity="0.5" />
          <path d="M848 356 C842 326 826 308 814 288" fill="none" stroke="#9a8460" strokeWidth="1.2" opacity="0.45" />
          <ellipse cx="868" cy="358" rx="28" ry="6" fill="#163e3a" opacity="0.7" />
        </g>

        <g className="reef-sway" strokeLinecap="round" style={{ animationDuration: "9.4s", animationDelay: "-1.5s" }}>
          <path d="M1040 340 C1026 286 1008 250 1016 206" fill="none" stroke="var(--coral)" strokeWidth="3.4" opacity="0.72" />
          <path d="M1048 318 C1068 274 1058 236 1076 206" fill="none" stroke="#d85a4c" strokeWidth="2" opacity="0.65" />
          <path d="M1056 308 C1080 268 1100 240 1110 210" fill="none" stroke="#c9843a" strokeWidth="1.7" opacity="0.6" />
          <path d="M1032 280 C1018 258 1024 236 1012 216" fill="none" stroke="var(--coral)" strokeWidth="1.3" opacity="0.55" />
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
