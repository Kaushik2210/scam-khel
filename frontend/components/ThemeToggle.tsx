"use client";

import { useI18n, type Key } from "@/lib/i18n";
import { useTheme, type Theme } from "@/lib/theme";

const OPTIONS: { id: Theme; key: Key; path: string }[] = [
  { id: "light", key: "theme.light", path: "M12 4V2m0 20v-2M4 12H2m20 0h-2M6 6L4.500 4.500M19.500 19.500L18 18M6 18l-1.500 1.500M19.500 4.500L18 6M12 8a4 4 0 100 8 4 4 0 000-8z" },
  { id: "system", key: "theme.system", path: "M4 5h16v11H4zM9 20h6M12 16v4" },
  { id: "dark", key: "theme.dark", path: "M20 14.500A8 8 0 019.500 4 8 8 0 1020 14.500z" },
];

/** Segmented control: Light / Auto / Dark. Each segment is a labelled, 44px-tall radio. */
export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const { t } = useI18n();
  return (
    <div role="radiogroup" aria-label={t("theme.label")} className="inline-flex rounded-ctl bg-raised p-1">
      {OPTIONS.map((o) => (
        <button
          key={o.id}
          type="button"
          role="radio"
          aria-checked={theme === o.id}
          aria-label={t(o.key)}
          title={t(o.key)}
          data-testid={`theme-${o.id}`}
          onClick={() => setTheme(o.id)}
          className={`flex h-9 min-w-9 items-center justify-center rounded-[9px] px-2.5 ${
            theme === o.id ? "bg-surface text-label shadow" : "text-label2 hover:text-label"
          }`}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d={o.path} />
          </svg>
        </button>
      ))}
    </div>
  );
}
