"use client";

import { useEffect, useRef } from "react";

/** Soft ring that trails the mouse and swells over interactive elements. Mouse users only; off for Reduce Motion. */
export function CursorRing() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const fine = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!fine || calm) return;
    let x = -100;
    let y = -100;
    let rx = x;
    let ry = y;
    let raf = 0;
    const move = (e: MouseEvent) => {
      x = e.clientX;
      y = e.clientY;
      el.dataset.on = "true";
      const hot = (e.target as Element | null)?.closest("a,button,summary,label,select,[role=button]");
      el.dataset.hot = hot ? "true" : "false";
    };
    const leave = () => (el.dataset.on = "false");
    const tick = () => {
      rx += (x - rx) * 0.18;
      ry += (y - ry) * 0.18;
      el.style.transform = `translate3d(${rx}px, ${ry}px, 0)`;
      raf = requestAnimationFrame(tick);
    };
    window.addEventListener("mousemove", move, { passive: true });
    document.addEventListener("mouseleave", leave);
    raf = requestAnimationFrame(tick);
    return () => {
      window.removeEventListener("mousemove", move);
      document.removeEventListener("mouseleave", leave);
      cancelAnimationFrame(raf);
    };
  }, []);
  return <div ref={ref} className="cursor-ring" aria-hidden="true" data-on="false" data-hot="false" />;
}
