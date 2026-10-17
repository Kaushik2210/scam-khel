"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Icon } from "@/components/Icon";
import { useRequireConsent } from "@/components/Consent";
import { useI18n, type Key } from "@/lib/i18n";
import { TACTICS, lab } from "@/lib/labels";

const SAMPLE_TACTICS = ["authority_impersonation", "fear_arrest_threat", "stay_on_camera_digital_arrest", "safe_account_transfer"];

function SampleCard() {
  const { t, lang } = useI18n();
  const score = 92;
  const R = 80;
  const C = Math.PI * R;
  return (
    <aside className="card w-full max-w-sm shadow-lg" aria-label={t("home.sample.title")}>
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-headline">{t("home.sample.title")}</h2>
        <span className="chip">{t("home.sample.note")}</span>
      </div>
      <svg viewBox="0 0 200 118" className="mx-auto w-full max-w-[240px]" role="img" aria-label={`${t("panel.risk")}: ${t("risk.critical")}, ${score}`}>
        <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="var(--raised)" strokeWidth="14" strokeLinecap="round" />
        <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="var(--crit)" strokeWidth="14" strokeLinecap="round" strokeDasharray={C} strokeDashoffset={C * (1 - score / 100)} />
        <text x="100" y="92" textAnchor="middle" fontSize="40" fontWeight="700" fill="var(--label)">
          {score}
        </text>
        <text x="100" y="112" textAnchor="middle" fontSize="12" fill="var(--label-2)">
          {t("risk.of")}
        </text>
      </svg>
      <p className="mt-1 flex items-center justify-center gap-2 text-title2">
        <Icon name="alert" size={22} /> {t("risk.critical")}
      </p>
      <ul className="mt-3 flex flex-wrap justify-center gap-1.5">
        {SAMPLE_TACTICS.map((x) => (
          <li key={x} className="rounded-full bg-danger-bg px-2.5 py-1 text-footnote">
            {lab(TACTICS, x, lang)}
          </li>
        ))}
      </ul>
    </aside>
  );
}

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
  const trust = ["trust.private", "trust.encrypted", "trust.sim", "trust.draft"] as const;
  return (
    <div className="space-y-14">
      <section className="grid items-center gap-8 pt-4 lg:grid-cols-[1.25fr_1fr]">
        <div>
          <h1 className="text-large md:text-[2.75rem] md:leading-[1.15]">{t("home.title")}</h1>
          <p className="mt-4 max-w-2xl text-body text-label2">{t("home.sub")}</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <button type="button" className="btn-primary !min-h-[52px] !px-7" onClick={() => go("/live")} data-testid="cta-check">
              <Icon name="shield" /> {t("home.cta.check")}
            </button>
            <button type="button" className="btn-secondary !min-h-[52px] !px-7" onClick={() => go("/simulate")} data-testid="cta-sim">
              <Icon name="play" /> {t("home.cta.sim")}
            </button>
          </div>
          <ul className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-footnote text-label2">
            {trust.map((k) => (
              <li key={k} className="flex items-center gap-1.5">
                <span className="text-ok">
                  <Icon name="check" size={16} />
                </span>
                {t(k)}
              </li>
            ))}
          </ul>
        </div>
        <div className="flex justify-center lg:justify-end">
          <SampleCard />
        </div>
      </section>

      <section aria-label="Features" className="grid gap-4 md:grid-cols-2">
        {(
          [
            ["/live", "home.feature.listen", "home.feature.listenD", "mic"],
            ["/report", "home.feature.report", "home.feature.reportD", "doc"],
          ] as const
        ).map(([href, h, d, icon]) => (
          <Link key={href} href={href} className="card group flex items-start gap-4 transition-colors hover:bg-raised">
            <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-tint text-tint-on">
              <Icon name={icon} size={24} />
            </span>
            <span>
              <span className="block text-headline">{t(h)}</span>
              <span className="mt-0.5 block text-callout text-label2">{t(d)}</span>
            </span>
          </Link>
        ))}
      </section>

      <section aria-label="How it works" className="grid gap-4 md:grid-cols-3">
        {steps.map(([h, d, icon], i) => (
          <div key={h} className="card">
            <div className="mb-3 flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-tint text-tint-on">
                <Icon name={icon} size={20} />
              </span>
              <span className="text-footnote font-semibold text-label3">0{i + 1}</span>
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
          <Link href="/parent" className="card block min-h-[7rem] transition-colors hover:bg-raised">
            <span className="mb-2 flex items-center gap-2 text-headline">
              <Icon name="phone" /> {t("home.mode.parent")}
            </span>
            <span className="text-callout text-label2">{t("home.mode.parentD")}</span>
          </Link>
        </div>
      </section>
      <section aria-labelledby="faq">
        <h2 id="faq" className="mb-3 text-title2">
          {t("faq.title")}
        </h2>
        <div className="divide-y divide-[var(--separator)] overflow-hidden rounded-card border border-sep bg-surface">
          {([1, 2, 3, 4] as const).map((n) => (
            <details key={n} className="group p-4 open:bg-raised">
              <summary className="flex min-h-tap cursor-pointer list-none items-center justify-between gap-3 text-headline">
                {t(`faq.q${n}` as Key)}
                <span className="text-label3 transition-transform group-open:rotate-45" aria-hidden="true">
                  +
                </span>
              </summary>
              <p className="mt-2 text-callout text-label2">{t(`faq.a${n}` as Key)}</p>
            </details>
          ))}
        </div>
      </section>
      <p className="text-callout text-label3">{t("home.demoNote")}</p>
    </div>
  );
}
