"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "./Icon";
import { useI18n, type Key } from "@/lib/i18n";

const TABS: { href: string; key: Key; icon: string; match: (p: string) => boolean }[] = [
  { href: "/", key: "nav.home", icon: "home", match: (p) => p === "/" },
  { href: "/simulate", key: "nav.simulate", icon: "play", match: (p) => p.startsWith("/simulate") },
  { href: "/live", key: "nav.shield", icon: "shield", match: (p) => p.startsWith("/live") },
  { href: "/incidents", key: "nav.incidents", icon: "doc", match: (p) => p.startsWith("/incidents") },
  {
    href: "/more",
    key: "nav.more",
    icon: "more",
    match: (p) => ["/more", "/family", "/memory", "/about"].some((x) => p.startsWith(x)),
  },
];

export function LanguageToggle() {
  const { lang, setLang, t } = useI18n();
  return (
    <button
      type="button"
      className="btn-secondary !min-h-tap !px-4 !text-callout"
      onClick={() => setLang(lang === "en" ? "hi" : "en")}
      aria-label={t("lang.switchLabel")}
      lang={lang === "en" ? "hi" : "en"}
    >
      <Icon name="globe" size={18} />
      {t("lang.switch")}
    </button>
  );
}

/** Desktop: top bar. Phone: bottom tab bar for the 5 peer sections (HIG tab bar pattern). */
export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname() ?? "/";
  const { t } = useI18n();
  if (path.startsWith("/parent")) return <>{children}</>; // Parent view is chrome-free by design
  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 pb-24 md:pb-8">
      <header className="flex items-center justify-between gap-3 py-4">
        <Link href="/" className="flex items-center gap-2 text-headline" aria-label={t("brand")}>
          <span className="text-tint">
            <Icon name="shield" size={26} />
          </span>
          {t("brand")}
        </Link>
        <nav aria-label="Primary" className="hidden items-center gap-1 md:flex">
          {TABS.map((tab) => (
            <Link
              key={tab.href}
              href={tab.href}
              aria-current={tab.match(path) ? "page" : undefined}
              className={`flex min-h-tap items-center rounded-ctl px-4 text-callout font-semibold ${
                tab.match(path) ? "bg-raised text-label" : "text-label2 hover:text-label"
              }`}
            >
              {t(tab.key)}
            </Link>
          ))}
        </nav>
        <LanguageToggle />
      </header>
      <main id="main" className="flex-1">
        {children}
      </main>
      <footer className="mt-10 border-t border-sep pt-4 text-footnote text-label3">
        {t("common.draft")}
      </footer>
      <nav
        aria-label="Primary"
        className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-sep bg-surface pb-[env(safe-area-inset-bottom)] md:hidden"
      >
        {TABS.map((tab) => (
          <Link
            key={tab.href}
            href={tab.href}
            aria-current={tab.match(path) ? "page" : undefined}
            className={`flex min-h-[56px] flex-col items-center justify-center gap-0.5 text-caption font-semibold ${
              tab.match(path) ? "text-tint" : "text-label2"
            }`}
          >
            <Icon name={tab.icon} size={22} />
            {t(tab.key)}
          </Link>
        ))}
      </nav>
    </div>
  );
}
