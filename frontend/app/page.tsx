"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Icon } from "@/components/Icon";
import { useRequireConsent } from "@/components/Consent";
import { useI18n } from "@/lib/i18n";

export default function Home() {
  const { t } = useI18n();
  const router = useRouter();
  const requireConsent = useRequireConsent();
  const go = async (href: string) => {
    if (await requireConsent()) router.push(href);
  };
  const steps = [
    ["home.step1", "home.step1d", "shield"],
    ["home.step2", "home.step2d", "clock"],
    ["home.step3", "home.step3d", "users"],
  ] as const;
  const modes = [
    ["/live", "home.mode.shield", "home.mode.shieldD", "shield"],
    ["/simulate", "home.mode.sim", "home.mode.simD", "play"],
  ] as const;
  return (
    <div className="space-y-10">
      <section className="pt-4">
        <h1 className="max-w-3xl text-large md:text-[2.5rem] md:leading-tight">{t("home.title")}</h1>
        <p className="mt-3 max-w-2xl text-body text-label2">{t("home.sub")}</p>
      </section>

      <section aria-label="How it works" className="grid gap-3 md:grid-cols-3">
        {steps.map(([h, d, icon], i) => (
          <div key={h} className="card">
            <div className="mb-2 flex items-center gap-2 text-tint">
              <Icon name={icon} size={24} />
              <span className="text-footnote font-semibold text-label2">{i + 1}</span>
            </div>
            <h2 className="text-headline">{t(h)}</h2>
            <p className="mt-1 text-callout text-label2">{t(d)}</p>
          </div>
        ))}
      </section>

      <section aria-labelledby="pick">
        <h2 id="pick" className="mb-3 text-title2">
          {t("home.pick")}
        </h2>
        <div className="grid gap-3 md:grid-cols-3">
          {modes.map(([href, h, d, icon]) => (
            <button
              key={href}
              type="button"
              onClick={() => go(href)}
              data-testid={`mode-${href.slice(1)}`}
              className="card min-h-[7rem] text-left transition-colors hover:bg-raised"
            >
              <span className="mb-2 flex items-center gap-2 text-headline">
                <Icon name={icon} /> {t(h)}
              </span>
              <span className="text-callout text-label2">{t(d)}</span>
            </button>
          ))}
          <Link href="/parent" className="card block min-h-[7rem] hover:bg-raised">
            <span className="mb-2 flex items-center gap-2 text-headline">
              <Icon name="phone" /> {t("home.mode.parent")}
            </span>
            <span className="text-callout text-label2">{t("home.mode.parentD")}</span>
          </Link>
        </div>
      </section>
      <p className="text-callout text-label3">{t("home.demoNote")}</p>
    </div>
  );
}
