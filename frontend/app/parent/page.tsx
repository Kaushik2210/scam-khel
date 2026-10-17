"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRequireConsent } from "@/components/Consent";
import { MicButton } from "@/components/MicButton";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Notice } from "@/components/Panels";
import { EXAMPLES } from "@/lib/examples";
import { api, ApiError } from "@/lib/api";
import { useI18n } from "@/lib/i18n";

interface Verdict {
  level: "low" | "caution" | "high" | "critical";
  score: number;
  explanation: { summary: string; what_to_do: string[] };
}
interface PanicBundle {
  checklist: string[];
  call_script: string;
  complaint_markdown: string;
  transaction_form: Record<string, string>;
}

/** Elderly-friendly view: one task per screen area, 64px+ targets, large type, no jargon. */
export default function Parent() {
  const { t, lang, setLang } = useI18n();
  const requireConsent = useRequireConsent();
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [verdict, setVerdict] = useState<Verdict | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [panic, setPanic] = useState(false);
  const [bundle, setBundle] = useState<PanicBundle | null>(null);
  const [form, setForm] = useState({ amount: "", to: "", bank: "", ref: "", phone: "" });
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (window.location.hash === "#panic") setPanic(true);
  }, []);

  const check = async () => {
    if (!text.trim() || !(await requireConsent())) return;
    setBusy(true);
    setError(null);
    try {
      setVerdict(
        await api<Verdict>("/api/analyze", {
          method: "POST",
          body: JSON.stringify({ text, language: lang, consent: true }),
        }),
      );
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("common.error"));
    } finally {
      setBusy(false);
    }
  };

  const makePanic = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setBundle(
        await api<PanicBundle>("/api/panic", {
          method: "POST",
          body: JSON.stringify({
            language: lang,
            amount_inr: Number(form.amount),
            beneficiary_account_or_upi: form.to,
            bank_name: form.bank,
            txn_reference: form.ref,
            caller_phone: form.phone,
          }),
        }),
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("common.error"));
    } finally {
      setBusy(false);
    }
  };

  const scam = verdict && (verdict.level === "high" || verdict.level === "critical");
  return (
    <main className="mx-auto max-w-2xl space-y-8 px-4 py-6 text-[1.375rem] leading-8" id="main">
      <header className="flex items-center justify-between">
        <Link href="/" className="min-h-tapxl inline-flex items-center text-callout text-tint underline">
          ← {t("common.back")}
        </Link>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <button type="button" className="btn-secondary !min-h-tapxl" onClick={() => setLang(lang === "en" ? "hi" : "en")}>
            {t("lang.switch")}
          </button>
        </div>
      </header>

      <section aria-labelledby="q" className="space-y-4">
        <h1 id="q" className="text-large md:text-[2.5rem]">
          {t("parent.title")}
        </h1>
        <p className="text-label2">{t("parent.sub")}</p>
        <label htmlFor="pt" className="sr-only">
          {t("parent.title")}
        </label>
        <textarea
          id="pt"
          className="field min-h-[9rem] !text-[1.25rem] py-3"
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={8000}
          data-testid="parent-text"
        />
        <div className="flex flex-wrap gap-2">
          <MicButton big onText={(x) => setText((p) => (p ? p + " " : "") + x)} />
          <button type="button" className="btn-secondary !min-h-tapxl" onClick={() => setText(EXAMPLES[0].text[lang])}>
            {t("live.examples")}
          </button>
        </div>
        <button type="button" className="btn-primary !min-h-tapxl w-full !text-[1.5rem]" onClick={check} disabled={busy || !text.trim()}>
          {busy ? t("common.loading") : t("parent.check")}
        </button>
        {verdict && (
          <div
            role="status"
            className={`rounded-card p-5 ${scam ? "bg-crit-bg" : "bg-ok-bg"}`}
            data-testid="parent-verdict"
            data-level={verdict.level}
          >
            <p className="text-title1">{scam ? t("parent.scam") : t("parent.safe")}</p>
            {scam && (
              <>
                <ol className="mt-3 list-decimal space-y-2 pl-6">
                  {verdict.explanation.what_to_do.map((x) => (
                    <li key={x}>{x}</li>
                  ))}
                </ol>
                <a href="tel:1930" className="btn-danger !min-h-tapxl mt-4 w-full !text-[1.5rem]">
                  {t("panic.call")}
                </a>
              </>
            )}
          </div>
        )}
      </section>

      <section id="panic" aria-labelledby="pn" className="space-y-4 border-t border-sep pt-8">
        <button
          type="button"
          className="btn-danger !min-h-[5rem] w-full !text-[1.75rem]"
          onClick={() => setPanic((p) => !p)}
          aria-expanded={panic}
          aria-controls="panic-body"
          data-testid="panic-open"
        >
          {t("actions.panic")}
        </button>
        {panic && (
          <div id="panic-body" className="space-y-4">
            <h2 id="pn" className="text-title1">
              {t("panic.title")}
            </h2>
            <p className="text-label2">{t("panic.sub")}</p>
            <a href="tel:1930" className="btn-danger !min-h-tapxl w-full !text-[1.5rem]">
              {t("panic.call")}
            </a>
            {!bundle ? (
              <form onSubmit={makePanic} className="space-y-3">
                {(
                  [
                    ["amount", "panic.amount", "number"],
                    ["to", "panic.to", "text"],
                    ["bank", "panic.bank", "text"],
                    ["ref", "panic.ref", "text"],
                    ["phone", "panic.phone", "tel"],
                  ] as const
                ).map(([k, label, type]) => (
                  <label key={k} className="block">
                    <span className="mb-1 block text-callout font-semibold">{t(label)}</span>
                    <input
                      className="field !min-h-tapxl !text-[1.25rem]"
                      type={type}
                      inputMode={type === "number" ? "decimal" : undefined}
                      value={form[k]}
                      onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                      required={k === "amount"}
                      min={k === "amount" ? 1 : undefined}
                    />
                  </label>
                ))}
                <button type="submit" className="btn-primary !min-h-tapxl w-full !text-[1.5rem]" disabled={busy}>
                  {t("panic.make")}
                </button>
              </form>
            ) : (
              <div className="space-y-4" data-testid="panic-bundle">
                <ol className="list-decimal space-y-2 pl-6">
                  {bundle.checklist.map((x) => (
                    <li key={x}>{x}</li>
                  ))}
                </ol>
                <div className="card">
                  <h3 className="mb-2 text-title2">{t("panic.script")}</h3>
                  <p className="text-body">{bundle.call_script}</p>
                  <button
                    type="button"
                    className="btn-secondary !min-h-tapxl mt-3"
                    onClick={async () => {
                      try {
                        await navigator.clipboard.writeText(bundle.call_script);
                        setCopied(true);
                      } catch {
                        setCopied(false);
                      }
                    }}
                  >
                    {copied ? t("panic.copied") : t("panic.copy")}
                  </button>
                </div>
                <p className="text-callout text-label2">{t("common.draft")}</p>
              </div>
            )}
          </div>
        )}
        {error && <Notice tone="error">{error}</Notice>}
      </section>
    </main>
  );
}
