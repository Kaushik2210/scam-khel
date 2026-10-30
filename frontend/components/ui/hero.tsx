"use client";

import type { ReactNode } from "react";
import { MeshGradient } from "@paper-design/shaders-react";
import { motion, useReducedMotion } from "framer-motion";

type HeroProps = {
  title: string;
  sub: string;
  actions: ReactNode;
  footer?: ReactNode;
  aside?: ReactNode;
};

/** Shader-backed hero panel. Content is passed in so the page keeps its own text, buttons and handlers. */
export default function ShaderHero({ title, sub, actions, footer, aside }: HeroProps) {
  const reduce = useReducedMotion();
  const rise = (delay: number) =>
    reduce
      ? {}
      : { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.6, delay } };

  return (
    <section className="relative isolate overflow-hidden rounded-3xl bg-[#12082e] text-white">
      <div aria-hidden="true" className="absolute inset-0 -z-10">
        <MeshGradient
          className="absolute inset-0 h-full w-full"
          colors={["#1a0b3d", "#7c3aed", "#ec4899", "#14b8a6", "#f59e0b"]}
          speed={reduce ? 0 : 0.3}
        />
        <MeshGradient
          className="absolute inset-0 h-full w-full opacity-40"
          colors={["#12082e", "#ffffff", "#8b5cf6", "#f472b6"]}
          speed={reduce ? 0 : 0.2}
        />
        {/* keeps body text readable over the moving gradient */}
        <div className="absolute inset-0 bg-black/55 lg:bg-transparent lg:bg-gradient-to-r lg:from-black/75 lg:via-black/50 lg:to-black/20" />
      </div>

      <div className="grid items-center gap-8 p-6 sm:p-10 lg:grid-cols-[1.25fr_1fr] lg:p-14">
        <div>
          <motion.h1 className="text-large md:text-[2.75rem] md:leading-[1.15]" {...rise(0.2)}>
            {title}
          </motion.h1>
          <motion.p className="mt-4 max-w-2xl text-body text-white/80" {...rise(0.4)}>
            {sub}
          </motion.p>
          <motion.div className="mt-6 flex flex-wrap gap-3" {...rise(0.6)}>
            {actions}
          </motion.div>
          {footer}
        </div>
        {aside && <div className="flex justify-center text-label lg:justify-end">{aside}</div>}
      </div>
    </section>
  );
}
