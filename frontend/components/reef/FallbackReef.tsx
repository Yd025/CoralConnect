"use client";

import { useEffect, useState } from "react";
import type { ReefBand } from "@/lib/types";

export function useReefAsset(src: string) {
  const [ok, setOk] = useState(false);

  useEffect(() => {
    let cancel = false;
    setOk(false);
    fetch(src)
      .then((response) => {
        if (cancel) return;
        const type = response.headers.get("content-type") || "";
        setOk(response.ok && !type.includes("text/html"));
      })
      .catch(() => {
        if (!cancel) setOk(false);
      });
    return () => {
      cancel = true;
    };
  }, [src]);

  return ok;
}

export function BandArt({ band }: { band: ReefBand }) {
  const src = `/reef/${band}.svg`;
  const custom = useReefAsset(src);
  return (
    <div className={custom ? "reef__art is-custom" : "reef__art"}>
      <FallbackReef band={band} />
      {custom ? <img className="reef__custom" src={src} alt="" /> : null}
    </div>
  );
}

/**
 * Built-in tank. Replace this whole component, or drop band SVGs in
 * frontend/public/reef/ (thriving.svg, stressed.svg, bleaching.svg, dead.svg).
 * A file that loads covers this drawing. Game effects stay in ReefStage.
 */
export function FallbackReef({ band }: { band: ReefBand }) {
  return (
    <svg className="fallback-reef" viewBox="0 0 1200 700" preserveAspectRatio="xMidYMax slice" aria-hidden>
      <defs>
        <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#7fd4e8" />
          <stop offset="0.45" stopColor="#127a93" />
          <stop offset="1" stopColor="#063246" />
        </linearGradient>
        <linearGradient id="sand" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#e7c98a" />
          <stop offset="1" stopColor="#b8884e" />
        </linearGradient>
      </defs>
      <rect className="fallback-water" width="1200" height="700" fill="url(#water)" />
      <g opacity="0.35" stroke="#e9fff8" strokeWidth="8" fill="none">
        <path d="M180 0 C220 80 140 120 190 220" />
        <path d="M640 0 C690 90 600 140 660 250" />
        <path d="M980 0 C930 70 1020 130 960 230" />
      </g>
      <g className="fallback-coral" data-band={band}>
        <path d="M180 560 C170 470 140 430 190 360 C210 430 230 470 250 560 Z" fill="#ff6b7a" />
        <path d="M250 570 C260 480 300 390 340 340 C330 450 310 500 300 570 Z" fill="#ffb15a" />
        <path d="M430 580 C420 500 390 450 450 390 C470 460 490 510 500 580 Z" fill="#2ec4b6" />
        <path d="M520 575 C540 490 590 420 640 370 C620 470 590 520 580 575 Z" fill="#7d5cff" />
        <path d="M860 580 C840 490 800 430 860 350 C900 440 910 500 930 580 Z" fill="#ff5d8f" />
        <path d="M980 570 C1000 500 1060 450 1100 390 C1080 480 1050 530 1040 570 Z" fill="#3dd6c6" />
        <circle cx="210" cy="390" r="18" fill="#ffe08a" />
        <circle cx="470" cy="410" r="14" fill="#b6f27c" />
        <circle cx="900" cy="390" r="16" fill="#ffd6a5" />
      </g>
      <path className="fallback-floor" d="M0 560 C180 520 260 600 420 570 C620 530 760 610 980 560 C1100 530 1160 570 1200 550 L1200 700 L0 700 Z" fill="url(#sand)" />
      <g fill="#0d3b4c" opacity="0.35">
        <ellipse cx="220" cy="640" rx="70" ry="16" />
        <ellipse cx="760" cy="650" rx="110" ry="18" />
      </g>
    </svg>
  );
}

export function SceneProps() {
  return (
    <div className="reef__props" aria-hidden>
      <img className="prop prop-wave" src="/reef/12-little-wave.svg" alt="" />
      <img className="prop prop-light" src="/reef/13-harbor-lighthouse.svg" alt="" />
      <img className="prop prop-boat" src="/reef/14-buddy-boat.svg" alt="" />
      <img className="prop prop-stall" src="/reef/15-challenge-stall.svg" alt="" />
    </div>
  );
}

export function AmbientLife({ band = "thriving" }: { band?: ReefBand }) {
  const hurt = band === "bleaching" || band === "dead";
  const stressed = hurt || band === "stressed";
  return (
    <div className="reef__life" aria-hidden>
      <span className="swimmer s1 is-flip">
        <img src="/reef/04-pip-fish.svg" alt="" />
      </span>
      <span className="swimmer s2">
        <img src="/reef/04-pip-fish.svg" alt="" />
      </span>
      <span className="swimmer s3">
        <img src="/reef/03-juno-jellyfish.svg" alt="" />
      </span>
      {stressed ? null : (
        <span className="swimmer s-whale is-flip">
          <img src="/reef/06-winnie-whale.svg" alt="" />
        </span>
      )}
      {hurt ? null : (
        <span className="swimmer s-turtle">
          <img src="/reef/02-moss-turtle.svg" alt="" />
        </span>
      )}
      {stressed ? (
        <span className="swimmer s-trash">
          <img src="/reef/plastic-bag.svg" alt="" />
        </span>
      ) : null}
      {hurt ? (
        <>
          <span className="swimmer s-trash t2">
            <img src="/reef/crushed-bottle.svg" alt="" />
          </span>
          <span className="swimmer s-trash t3">
            <img src="/reef/fishbones-small.svg" alt="" />
          </span>
        </>
      ) : (
        <span className="swimmer s-octo">
          <img src="/reef/05-otto-octopus.svg" alt="" />
        </span>
      )}
      <i className="bubble b1" />
      <i className="bubble b2" />
      <i className="bubble b3" />
      <i className="bubble b4" />
    </div>
  );
}

export function Fish() {
  return (
    <svg width="86" height="42" viewBox="0 0 86 42">
      <ellipse cx="40" cy="21" rx="24" ry="12" fill="#f4d35e" />
      <path d="M62 21 L82 8 L78 21 L82 34 Z" fill="#ee964b" />
      <circle cx="28" cy="18" r="2.2" fill="#123" />
    </svg>
  );
}

export function Turtle() {
  return (
    <svg width="120" height="78" viewBox="0 0 120 78">
      <ellipse cx="58" cy="40" rx="28" ry="20" fill="#2a9d8f" />
      <ellipse cx="58" cy="40" rx="16" ry="11" fill="#8ecf8a" />
      <circle cx="92" cy="34" r="10" fill="#1d6a62" />
      <circle cx="95" cy="32" r="1.6" fill="#fff" />
      <path d="M40 24 l-16 -10 M40 54 l-14 12 M76 24 l10 -12 M76 56 l12 10" stroke="#1d6a62" strokeWidth="4" strokeLinecap="round" />
    </svg>
  );
}

export function Bloom() {
  return (
    <svg width="100" height="100" viewBox="0 0 100 100">
      <path d="M50 90 C48 60 30 50 28 28" stroke="#c94c6a" strokeWidth="8" fill="none" strokeLinecap="round" />
      <circle cx="28" cy="24" r="12" fill="#ff8fa3" />
      <circle cx="42" cy="18" r="8" fill="#ffd166" />
      <circle cx="18" cy="34" r="7" fill="#ffb4a2" />
    </svg>
  );
}

const TRASH = [
  "/reef/crushed-bottle.svg",
  "/reef/plastic-bag.svg",
  "/reef/discarded-cup.svg",
  "/reef/torn-wrapper.svg",
  "/reef/plastic-fragments.svg",
  "/reef/fishbones-large.svg",
];

export function SludgeBarrel({ seed = "sludge" }: { seed?: string }) {
  let pick = 0;
  for (const char of seed) pick = (pick + char.charCodeAt(0)) % TRASH.length;
  return (
    <div className="barrel" aria-hidden>
      <img src={TRASH[pick]} alt="" />
    </div>
  );
}
