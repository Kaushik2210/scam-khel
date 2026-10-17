"use client";

import { useState } from "react";
import { Card, Empty, Notice, Spinner } from "@/components/Panels";
import { api, ApiError } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useFetch } from "@/lib/useFetch";

interface Family {
  telegram_configured: boolean;
  members: { id: number; label: string; role: string; join_code: string; linked: boolean }[];
}

export default function FamilyPage() {
  const { t } = useI18n();
  const { data, error, loading, reload } = useFetch<Family>("/api/family");
  const [label, setLabel] = useState("");
  const [msg, setMsg] = useState<{ tone: "info" | "error"; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    setMsg(null);
    try {
      await fn();
    } catch (e) {
      setMsg({ tone: "error", text: e instanceof ApiError ? e.message : t("common.error") });
    } finally {
      setBusy(false);
    }
  };
  const add = (e: React.FormEvent) => {
    e.preventDefault();
    if (!label.trim()) return;
    run(async () => {
      await api("/api/family", { method: "POST", body: JSON.stringify({ label: label.trim() }) });
      setLabel("");
      reload();
    });
  };
  const test = () =>
    run(async () => {
      const r = await api<{ sent: number; skipped: string | null }>("/api/family/test-alert", { method: "POST" });
      setMsg({ tone: "info", text: r.sent > 0 ? t("family.testOk") : `Not sent: ${r.skipped ?? "no recipients"}` });
    });

  return (
    <div className="space-y-4">
      <h1 className="text-title1">{t("family.title")}</h1>
      <p className="text-callout text-label2">{t("family.sub")}</p>
      {loading && <Spinner label={t("common.loading")} />}
      {error && <Notice tone="error">{error}</Notice>}
      {data && !data.telegram_configured && <Notice tone="warn">{t("family.noTelegram")}</Notice>}
      {msg && <Notice tone={msg.tone}>{msg.text}</Notice>}
      <Card title={t("family.add")}>
        <form onSubmit={add} className="flex flex-col gap-2 sm:flex-row">
          <label className="sr-only" htmlFor="fl">
            {t("family.label")}
          </label>
          <input id="fl" className="field" value={label} onChange={(e) => setLabel(e.target.value)} placeholder={t("family.label")} maxLength={32} />
          <button type="submit" className="btn-primary" disabled={busy || !label.trim()}>
            {t("family.add")}
          </button>
        </form>
      </Card>
      <Card
        title={t("family.title")}
        right={
          <button type="button" className="btn-secondary" onClick={test} disabled={busy || !data?.telegram_configured}>
            {t("family.test")}
          </button>
        }
      >
        {data && data.members.length === 0 && <Empty>{t("family.empty")}</Empty>}
        <ul className="space-y-3">
          {(data?.members ?? []).map((m) => (
            <li key={m.id} className="flex flex-wrap items-center gap-3 border-b border-sep pb-3 last:border-0">
              <span className="text-headline">{m.label}</span>
              <span className={`chip ${m.linked ? "!bg-ok-bg" : "!bg-warn-bg"}`}>
                {m.linked ? t("family.linked") : t("family.pending")}
              </span>
              {!m.linked && (
                <span className="text-callout text-label2">
                  {t("family.how")} <code className="rounded bg-raised px-2 py-1 font-mono">/start {m.join_code}</code>
                </span>
              )}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
