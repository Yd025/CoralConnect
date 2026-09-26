"use client";

import { useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";

type Ripple = { id: number; x: number; y: number };

function isControl(target: EventTarget | null) {
  return target instanceof Element && Boolean(target.closest("a, button, input, textarea, select, label"));
}

function Anchor({
  className,
  layer,
  children,
}: {
  className: string;
  layer: number;
  children: ReactNode;
}) {
  return (
    <div
      className={`ambient-parallax scene-anchor ${className}`}
      style={{ ["--depth" as string]: 0, ["--layer" as string]: layer }}
    >
      <span className="scene-plant">{children}</span>
    </div>
  );
}

function Lane({
  className,
  top,
  depth,
  layer,
  pace,
  wave,
  direction = 1,
  children,
}: {
  className: string;
  top: string;
  depth: number;
  layer: number;
  pace: number;
  wave: number;
  direction?: 1 | -1;
  children: ReactNode;
}) {
  return (
    <div
      className={`ambient-parallax ${className}`}
      style={{ top, ["--depth" as string]: depth, ["--layer" as string]: layer }}
    >
      <span
        className="ambient-track swim"
        data-dir={direction}
        data-pace={pace}
        data-wave={wave}
        style={{ ["--fade" as string]: 1 }}
      >
        {children}
      </span>
    </div>
  );
}

function Cast({ src, flip, still }: { src: string; flip?: boolean; still?: boolean }) {
  const img = (
    <img
      className={["cast-art", flip ? "cast-flip" : "", still ? "cast-still" : ""].filter(Boolean).join(" ")}
      src={src}
      alt=""
    />
  );
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

  useLayoutEffect(() => {
    const node = rootRef.current;
    if (!node) return;

    const point = { x: 0, y: 0 };
    let frame = 0;
    let lastRipple = 0;
    let last = performance.now();
    const timers = new Set<number>();
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const nodes = [...node.querySelectorAll<HTMLElement>(".swim")];
    const swimmers = nodes.map((el, index) => {
      const dir = Number(el.dataset.dir) >= 0 ? 1 : -1;
      const cruise = Number(el.dataset.pace) || 28;
      const amp = Number(el.dataset.wave) || 80;
      const pace = cruise * (0.72 + Math.random() * 0.56);
      const view = window.innerWidth;
      const slot = ((index + 0.35) / nodes.length) * (view * 1.4) - view * 0.2;
      return {
        el,
        x: slot + (Math.random() - 0.5) * 36,
        y: (Math.random() - 0.5) * amp * 0.35,
        vx: dir * pace,
        vy: (Math.random() - 0.5) * 8,
        want: dir * pace,
        dir,
        cruise,
        amp,
        steer: Math.random() * 2 - 1,
        rise: 16 + Math.random() * 22,
        retarget: performance.now() + Math.random() * 4000,
      };
    });

    const members = [...node.querySelectorAll<HTMLElement>(".school-fish")].map((el) => {
      const homeX = parseFloat(el.style.left) || 0;
      const homeY = parseFloat(el.style.top) || 0;
      return {
        el,
        homeX,
        homeY,
        x: homeX + (Math.random() - 0.5) * 24,
        y: homeY + (Math.random() - 0.5) * 16,
        vx: (Math.random() - 0.5) * 8,
        vy: (Math.random() - 0.5) * 6,
        aimX: (Math.random() - 0.5) * 18,
        aimY: (Math.random() - 0.5) * 14,
        retarget: performance.now() + Math.random() * 2800,
      };
    });

    const placeMembers = () => {
      members.forEach((member) => {
        member.el.style.transform = `translate3d(${(member.x - member.homeX).toFixed(1)}px, ${(member.y - member.homeY).toFixed(1)}px, 0)`;
      });
    };

    const place = () => {
      swimmers.forEach((swimmer) => {
        swimmer.el.style.transform = `translate3d(${swimmer.x.toFixed(1)}px, ${swimmer.y.toFixed(1)}px, 0)`;
      });
    };

    const shove = (cx: number, cy: number, px: number, py: number, zone: number) => {
      let dx = cx - px;
      let dy = cy - py;
      let dist = Math.hypot(dx, dy);
      if (dist >= zone) return null;
      if (dist < 1) {
        dx = 0;
        dy = -1;
        dist = 1;
      }
      const impulse = (zone - dist) * 1.7;
      return { vx: (dx / dist) * impulse, vy: (dy / dist) * impulse };
    };

    const nudge = (px: number, py: number) => {
      members.forEach((member) => {
        const box = member.el.getBoundingClientRect();
        const hit = shove(box.left + box.width / 2, box.top + box.height / 2, px, py, Math.min(box.width, box.height) * 0.22 + 78);
        if (!hit) return;
        member.vx += hit.vx * 0.45;
        member.vy += hit.vy * 0.45;
        const speed = Math.hypot(member.vx, member.vy);
        if (speed > 80) {
          member.vx *= 80 / speed;
          member.vy *= 80 / speed;
        }
      });
      swimmers.forEach((swimmer) => {
        if (swimmer.el.querySelector(".school")) return;
        let nearest: { vx: number; vy: number } | null = null;
        for (const img of swimmer.el.querySelectorAll("img")) {
          const box = img.getBoundingClientRect();
          const hit = shove(
            box.left + box.width / 2,
            box.top + box.height / 2,
            px,
            py,
            Math.min(box.width, box.height) * 0.22 + 78,
          );
          if (hit && (!nearest || Math.hypot(hit.vx, hit.vy) > Math.hypot(nearest.vx, nearest.vy))) nearest = hit;
        }
        if (!nearest) return;
        swimmer.vy += nearest.vy;
        const shoved = swimmer.vx + nearest.vx * 0.4;
        if (shoved * swimmer.dir < swimmer.cruise * 0.18) {
          swimmer.vy += Math.sign(nearest.vy || -1) * Math.abs(nearest.vx) * 0.65;
          swimmer.vx = swimmer.dir * swimmer.cruise * 0.18;
        } else {
          swimmer.vx = shoved;
        }
      });
    };

    const step = (now: number) => {
      const dt = Math.min(0.05, (now - last) / 1000 || 0.016);
      last = now;
      node.style.setProperty("--px", point.x.toFixed(4));
      node.style.setProperty("--py", point.y.toFixed(4));
      if (reduced) return;

      const view = window.innerWidth;
      swimmers.forEach((swimmer) => {
        if (now > swimmer.retarget) {
          swimmer.steer = Math.random() * 2 - 1;
          swimmer.want = swimmer.dir * swimmer.cruise * (0.68 + Math.random() * 0.64);
          swimmer.retarget = now + 2400 + Math.random() * 6200;
        }
        if (swimmer.y > swimmer.amp) swimmer.steer = Math.min(swimmer.steer, -0.35);
        if (swimmer.y < -swimmer.amp) swimmer.steer = Math.max(swimmer.steer, 0.35);
        swimmer.vx += (swimmer.want - swimmer.vx) * Math.min(1, dt * 0.28);
        swimmer.vy += (swimmer.steer * swimmer.rise - swimmer.vy) * Math.min(1, dt * 0.45);
        swimmer.x += swimmer.vx * dt;
        swimmer.y += swimmer.vy * dt;

        const span = swimmer.el.offsetWidth || 220;
        if (swimmer.dir > 0 && swimmer.x > view + span) {
          swimmer.x = -span - Math.random() * 320;
          swimmer.y = (Math.random() - 0.5) * swimmer.amp;
          swimmer.vy = 0;
          swimmer.want = swimmer.dir * swimmer.cruise * (0.7 + Math.random() * 0.5);
          swimmer.vx = swimmer.want;
        } else if (swimmer.dir < 0 && swimmer.x < -span) {
          swimmer.x = view + Math.random() * 320;
          swimmer.y = (Math.random() - 0.5) * swimmer.amp;
          swimmer.vy = 0;
          swimmer.want = swimmer.dir * swimmer.cruise * (0.7 + Math.random() * 0.5);
          swimmer.vx = swimmer.want;
        }
      });

      const bodies = swimmers.map((swimmer) => {
        const box = swimmer.el.getBoundingClientRect();
        return {
          swimmer,
          cx: box.left + box.width / 2,
          cy: box.top + box.height / 2,
          w: box.width,
          h: box.height,
        };
      });
      for (let i = 0; i < bodies.length; i += 1) {
        for (let j = i + 1; j < bodies.length; j += 1) {
          const a = bodies[i];
          const b = bodies[j];
          let dx = a.cx - b.cx;
          let dy = a.cy - b.cy;
          const overlapX = (Math.min(a.w, 340) + Math.min(b.w, 340)) / 2 - Math.abs(dx);
          const overlapY = (Math.min(a.h, 260) + Math.min(b.h, 260)) / 2 - Math.abs(dy);
          if (overlapX <= 0 || overlapY <= 0) continue;
          const dist = Math.max(1, Math.hypot(dx, dy));
          dx /= dist;
          dy /= dist;
          const push = Math.min(90, Math.min(overlapX, overlapY) * 2.2) * dt;
          a.swimmer.vy = Math.max(-70, Math.min(70, a.swimmer.vy + dy * push));
          b.swimmer.vy = Math.max(-70, Math.min(70, b.swimmer.vy - dy * push));
          a.swimmer.want = a.swimmer.dir * Math.min(a.swimmer.cruise * 1.35, Math.abs(a.swimmer.want) + push * 0.35);
          b.swimmer.want = b.swimmer.dir * Math.min(b.swimmer.cruise * 1.35, Math.abs(b.swimmer.want) + push * 0.35);
        }
      }

      members.forEach((member) => {
        if (now > member.retarget) {
          member.aimX = (Math.random() - 0.5) * 12;
          member.aimY = (Math.random() - 0.5) * 10;
          member.retarget = now + 2000 + Math.random() * 4800;
        }
        const ox = member.homeX - member.x;
        const oy = member.homeY - member.y;
        const off = Math.hypot(ox, oy);
        const gain = 0.28 + Math.min(0.55, off / 150);
        const pullX = ox * gain + member.aimX;
        const pullY = oy * gain + member.aimY;
        member.vx += (pullX - member.vx) * Math.min(1, dt * 1.6);
        member.vy += (pullY - member.vy) * Math.min(1, dt * 1.6);
        member.x += member.vx * dt;
        member.y += member.vy * dt;
      });
      place();
      placeMembers();
    };

    place();
    placeMembers();
    const loop = (now: number) => {
      frame = requestAnimationFrame(loop);
      step(now);
    };
    frame = requestAnimationFrame(loop);

    const onMove = (event: PointerEvent) => {
      point.x = (event.clientX / window.innerWidth - 0.5) * 2;
      point.y = (event.clientY / window.innerHeight - 0.5) * 2;
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
      if (!reduced) nudge(pointer.clientX, pointer.clientY);
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
        <Lane className="cast-jelly" top="16%" depth={0.35} layer={3} pace={24} wave={100}>
          <Cast src="/reef/03-juno-jellyfish.svg" />
        </Lane>
        <Lane className="cast-whale" top="6%" depth={0.5} layer={4} pace={16} wave={70}>
          <Cast src="/reef/06-winnie-whale.svg" flip />
        </Lane>
        <Lane className="cast-turtle" top="34%" depth={0.7} layer={5} pace={28} wave={110}>
          <Cast src="/reef/02-moss-turtle.svg" />
        </Lane>
        <Lane className="cast-tang cast-tang-far" top="24%" depth={0.4} layer={3} pace={32} wave={80}>
          <Cast src="/reef/04-pip-fish.svg" flip />
        </Lane>
        <Lane className="cast-tang" top="48%" depth={0.95} layer={6} pace={38} wave={60} direction={-1}>
          <Cast src="/reef/04-pip-fish.svg" />
        </Lane>
        <Lane className="cast-school" top="20%" depth={0.32} layer={3} pace={34} wave={90}>
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
        <Lane className="cast-school" top="40%" depth={0.62} layer={5} pace={40} wave={70} direction={-1}>
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
        <Lane className="cast-school" top="56%" depth={0.8} layer={6} pace={30} wave={120}>
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
        <Lane className="cast-octopus" top="60%" depth={0.45} layer={5} pace={18} wave={85} direction={-1}>
          <Cast src="/reef/05-otto-octopus.svg" />
        </Lane>
        <Anchor className="cast-crab" layer={7}>
          <Cast src="/reef/01-clover-crab.svg" still />
        </Anchor>
        <Anchor className="cast-coral" layer={7}>
          <Cast src="/reef/10-coral-bloom.svg" still />
        </Anchor>
        <Anchor className="cast-star" layer={7}>
          <Cast src="/reef/07-sunny-star.svg" still />
        </Anchor>
        <Anchor className="cast-shell" layer={7}>
          <Cast src="/reef/08-shell-badge.svg" still />
        </Anchor>
        <Anchor className="cast-kelp" layer={6}>
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
                ["--wave" as string]: "22px",
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
