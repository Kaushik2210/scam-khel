"use client";

import { useEffect, useRef } from "react";

/** Modal sheet / alert. Traps Tab, restores focus, Esc cancels (unless `locked`). */
export function Sheet({
  open,
  title,
  onClose,
  children,
  locked = false,
  labelId = "sheet-title",
}: {
  open: boolean;
  title: string;
  onClose?: () => void;
  children: React.ReactNode;
  locked?: boolean;
  labelId?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const prev = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!open) return;
    prev.current = document.activeElement as HTMLElement | null;
    const el = ref.current;
    const focusables = () =>
      Array.from(
        el?.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), textarea, select, [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      );
    focusables()[0]?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !locked) onClose?.();
      if (e.key === "Tab") {
        const f = focusables();
        if (!f.length) return;
        const first = f[0];
        const last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      prev.current?.focus?.();
    };
  }, [open, locked, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-0 sm:items-center sm:p-4">
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelId}
        className="anim-in max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-t-card bg-surface p-5 shadow-xl sm:rounded-card"
      >
        <h2 id={labelId} className="mb-3 text-title2">
          {title}
        </h2>
        {children}
      </div>
    </div>
  );
}
