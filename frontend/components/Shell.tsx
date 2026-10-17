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

const REPO = "https://github.com/Kaushik2210/scam-khel";

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

/** Always-visible emergency strip: the single most useful action if money has already left. */
function EmergencyBar() {
  const { t } = useI18n();
  return (
    <div className="bg-crit text-white" role="region" aria-label={t("emergency.text")}>
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-4 gap-y-1 px-4 py-2 text-callout">
        <span className="font-semibold">{t("emergency.text")}</span>
        <a href="tel:1930" className="inline-flex min-h-[32px] items-center rounded-full bg-white px-4 font-bold text-[#b3001b] underline-offset-2 hover:underline">
          <Icon name="phone" size={16} />
          <span className="ml-1.5">{t("emergency.cta")}</span>
        </a>
        <Link href="/parent#panic" className="underline underline-offset-2">
          {t("actions.panic")}
        </Link>
      </div>
    </div>
  );
}

/** Desktop: top bar. Phone: bottom tab bar for the 5 peer sections (HIG tab bar pattern). */
export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname() ?? "/";
  const { t } = useI18n();
  if (path.startsWith("/parent")) return <>{children}</>; // Parent view is chrome-free by design
  return (
    <>
      <EmergencyBar />
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 pb-24 md:pb-8">
        <header className="flex items-center justify-between gap-3 py-4">
          <Link href="/" className="flex items-center gap-2 text-headline" aria-label={t("brand")}>
            <span className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-tint text-tint-on">
              <Icon name="shield" size={22} />
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
          <div className="flex items-center gap-2">
            <Link href="/parent" className="btn-secondary !hidden !min-h-tap !px-4 !text-callout md:!inline-flex">
              <Icon name="phone" size={18} /> {t("nav.parent")}
            </Link>
            <LanguageToggle />
          </div>
        </header>
        <main id="main" className="flex-1">
          {children}
        </main>
        <footer className="mt-12 flex flex-col gap-3 border-t border-sep pt-5 text-footnote text-label3 md:flex-row md:items-center md:justify-between">
          <p>{t("common.draft")}</p>
          <nav aria-label="Footer" className="flex flex-wrap gap-x-5 gap-y-2">
            <Link href="/about" className="link-quiet">
              {t("nav.about")}
            </Link>
            <a href={`${REPO}/blob/main/PRIVACY.md`} className="link-quiet" target="_blank" rel="noopener noreferrer">
              {t("footer.privacy")}
            </a>
            <a href={`${REPO}/blob/main/SECURITY.md`} className="link-quiet" target="_blank" rel="noopener noreferrer">
              {t("footer.security")}
            </a>
            <a href={REPO} className="link-quiet" target="_blank" rel="noopener noreferrer">
              {t("footer.source")}
            </a>
          </nav>
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
    </>
  );
}
