"use client";

import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";

type Ripple = { id: number; x: number; y: number };

function isControl(target: EventTarget | null) {
  return target instanceof Element && Boolean(target.closest("a, button, input, textarea, select, label"));
}

function Anchor({
  className,
  depth,
  layer,
  drift,
  reverse,
  delay,
  children,
}: {
  className: string;
  depth: number;
  layer: number;
  drift: number;
  reverse?: boolean;
  delay?: number;
  children: ReactNode;
}) {
  return (
    <div
      className={`ambient-parallax scene-anchor ${className}`}
      style={{ ["--depth" as string]: depth, ["--layer" as string]: layer }}
    >
      <span
        className={reverse ? "ambient-track scene-drift is-reverse" : "ambient-track scene-drift"}
        style={{ animationDuration: `${drift}s`, animationDelay: `${delay ?? 0}s` }}
      >
        {children}
      </span>
    </div>
  );
}

function Lane({
  className,
  top,
  depth,
  layer,
  duration,
  delay,
  reverse,
  children,
}: {
  className: string;
  top: string;
  depth: number;
  layer: number;
  duration: number;
  delay: number;
  reverse?: boolean;
  children: ReactNode;
}) {
  return (
    <div
      className={`ambient-parallax ${className}`}
      style={{ top, ["--depth" as string]: depth, ["--layer" as string]: layer }}
    >
      <span
        className={reverse ? "ambient-track is-reverse" : "ambient-track"}
        style={{
          animationDuration: `${duration}s`,
          animationDelay: `${delay}s`,
          ["--fade" as string]: 1,
        }}
      >
        {children}
      </span>
    </div>
  );
}

function Cast({ src, flip, still }: { src: string; flip?: boolean; still?: boolean }) {
  const img = <img className={flip ? "cast-art cast-flip" : "cast-art"} src={src} alt="" />;
  return still ? img : <span className="avoid">{img}</span>;
}

function School({ flip, size, spots }: { flip?: boolean; size: number; spots: { x: number; y: number }[] }) {
  return (
    <span className="school">
      {spots.map((spot, index) => (
        <span key={index} className="avoid school-fish" style={{ left: spot.x, top: spot.y, width: size }}>
          <img className={flip ? "cast-art cast-flip" : "cast-art"} src="/reef/04-pip-fish.svg" alt="" />
        </span>
      ))}
    </span>
  );
}

function Mote({ size }: { size: number }) {
  return (
    <svg className="drifter-fish" width={size} height={size} viewBox="0 0 16 16">
      <circle cx="8" cy="8" r="3.2" fill="currentColor" />
    </svg>
  );
}

export function AnimatedBackground() {
  const rootRef = useRef<HTMLDivElement>(null);
  const ids = useRef(0);
  const [ripples, setRipples] = useState<Ripple[]>([]);

  useEffect(() => {
    const node = rootRef.current;
    if (!node) return;

    const point = { x: 0, y: 0, cx: 0, cy: 0, inside: false };
    const dodge = new WeakMap<HTMLElement, { x: number; y: number }>();
    let frame = 0;
    let lastRipple = 0;
    const timers = new Set<number>();

    const tick = () => {
      frame = 0;
      node.style.setProperty("--px", point.x.toFixed(4));
      node.style.setProperty("--py", point.y.toFixed(4));

      let settling = false;
      node.querySelectorAll<HTMLElement>(".avoid").forEach((el) => {
        const state = dodge.get(el) ?? { x: 0, y: 0 };
        const box = el.getBoundingClientRect();
        const left = box.left - state.x;
        const top = box.top - state.y;
        const cx = left + box.width / 2;
        const cy = top + box.height / 2;
        let dx = cx - point.cx;
        let dy = cy - point.cy;
        let dist = Math.hypot(dx, dy);
        const clear = Math.min(box.width, box.height) * 0.22 + 72;
        let tx = 0;
        let ty = 0;
        if (point.inside && dist < clear) {
          if (dist < 1) {
            dx = 0;
            dy = -1;
            dist = 1;
          }
          const push = clear - dist;
          tx = (dx / dist) * push;
          ty = (dy / dist) * push;
        }
        state.x += (tx - state.x) * 0.07;
        state.y += (ty - state.y) * 0.07;
        if (Math.hypot(state.x, state.y) > 0.6 || Math.hypot(tx, ty) > 0.6) settling = true;
        dodge.set(el, state);
        el.style.setProperty("--dodge-x", `${state.x.toFixed(1)}px`);
        el.style.setProperty("--dodge-y", `${state.y.toFixed(1)}px`);
      });

      if (settling) frame = requestAnimationFrame(tick);
    };

    const onMove = (event: PointerEvent) => {
      point.x = (event.clientX / window.innerWidth - 0.5) * 2;
      point.y = (event.clientY / window.innerHeight - 0.5) * 2;
      point.cx = event.clientX;
      point.cy = event.clientY;
      point.inside = true;
      if (frame === 0) frame = requestAnimationFrame(tick);
    };

    const onLeave = () => {
      point.inside = false;
      if (frame === 0) frame = requestAnimationFrame(tick);
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
      }, 2200);
      timers.add(timer);
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("pointerleave", onLeave);
    window.addEventListener("pointerdown", spawn, true);
    window.addEventListener("click", spawn, true);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerleave", onLeave);
      window.removeEventListener("pointerdown", spawn, true);
      window.removeEventListener("click", spawn, true);
      if (frame) cancelAnimationFrame(frame);
      timers.forEach((timer) => window.clearTimeout(timer));
    };
  }, []);

  const motes = [
    { id: "m1", top: "16%", size: 7, duration: 28, delay: -4, depth: 0.3, fade: 0.35 },
    { id: "m2", top: "30%", size: 5, duration: 22, delay: -12, depth: 0.55, fade: 0.28, reverse: true },
    { id: "m3", top: "44%", size: 8, duration: 34, delay: -8, depth: 0.2, fade: 0.22 },
  ];

  return (
    <>
      <div className="ambient" ref={rootRef} aria-hidden="true">
        <div className="ambient-parallax ambient-photo" style={{ ["--depth" as string]: 0.06, ["--layer" as string]: 0 }}>
          <img src="/reef/reef-backdrop.png" alt="" />
        </div>
        <Lane className="cast-jelly" top="16%" depth={0.35} layer={3} duration={72} delay={-16}>
          <Cast src="/reef/03-juno-jellyfish.svg" />
        </Lane>
        <Lane className="cast-whale" top="6%" depth={0.5} layer={4} duration={96} delay={-38}>
          <Cast src="/reef/06-winnie-whale.svg" flip />
        </Lane>
        <Lane className="cast-turtle" top="34%" depth={0.7} layer={5} duration={68} delay={-20}>
          <Cast src="/reef/02-moss-turtle.svg" />
        </Lane>
        <Lane className="cast-tang cast-tang-far" top="24%" depth={0.4} layer={3} duration={50} delay={-16}>
          <Cast src="/reef/04-pip-fish.svg" flip />
        </Lane>
        <Lane className="cast-tang" top="48%" depth={0.95} layer={6} duration={40} delay={-8} reverse>
          <Cast src="/reef/04-pip-fish.svg" />
        </Lane>
        <Lane className="cast-school" top="20%" depth={0.32} layer={3} duration={44} delay={-12}>
          <School
            flip
            size={150}
            spots={[
              { x: 0, y: 18 },
              { x: 78, y: -8 },
              { x: 86, y: 42 },
              { x: 156, y: 8 },
              { x: 168, y: 48 },
            ]}
          />
        </Lane>
        <Lane className="cast-school" top="40%" depth={0.62} layer={5} duration={38} delay={-20} reverse>
          <School
            size={130}
            spots={[
              { x: 0, y: 12 },
              { x: 70, y: -16 },
              { x: 74, y: 40 },
              { x: 140, y: 6 },
            ]}
          />
        </Lane>
        <Lane className="cast-school" top="56%" depth={0.8} layer={6} duration={56} delay={-26}>
          <School
            flip
            size={118}
            spots={[
              { x: 0, y: 16 },
              { x: 64, y: -6 },
              { x: 60, y: 38 },
              { x: 124, y: 10 },
              { x: 132, y: 42 },
              { x: 186, y: 4 },
            ]}
          />
        </Lane>
        <Lane className="cast-octopus" top="60%" depth={0.45} layer={5} duration={84} delay={-34} reverse>
          <Cast src="/reef/05-otto-octopus.svg" />
        </Lane>
        <Anchor className="cast-crab" depth={0.28} layer={7} drift={24} delay={-9}>
          <Cast src="/reef/01-clover-crab.svg" still />
        </Anchor>
        <Anchor className="cast-coral" depth={0.16} layer={7} drift={26}>
          <Cast src="/reef/10-coral-bloom.svg" still />
        </Anchor>
        <Anchor className="cast-star" depth={0.22} layer={7} drift={19} delay={-5}>
          <Cast src="/reef/07-sunny-star.svg" still />
        </Anchor>
        <Anchor className="cast-shell" depth={0.34} layer={7} drift={21} delay={-7}>
          <Cast src="/reef/08-shell-badge.svg" still />
        </Anchor>
        <Anchor className="cast-kelp" depth={0.18} layer={6} drift={17} reverse>
          <Cast src="/reef/11-seaweed-garden.svg" still />
        </Anchor>
        {motes.map((item) => (
          <div
            key={item.id}
            className="ambient-parallax"
            style={{
              top: item.top,
              ["--depth" as string]: item.depth,
              ["--layer" as string]: 3,
            } as CSSProperties}
          >
            <span
              className={item.reverse ? "ambient-track is-reverse" : "ambient-track"}
              style={{
                color: "#e7f7ff",
                animationDuration: `${item.duration}s`,
                animationDelay: `${item.delay}s`,
                ["--fade" as string]: item.fade,
              } as CSSProperties}
            >
              <Mote size={item.size} />
            </span>
          </div>
        ))}
        <div className="ambient-vignette" />
      </div>
      <div className="ambient-ripples" aria-hidden="true">
        {ripples.map((ripple) => (
          <span key={ripple.id} className="ambient-ripple" style={{ left: ripple.x, top: ripple.y }}>
            <i /><i /><i />
          </span>
        ))}
      </div>
    </>
  );
}
