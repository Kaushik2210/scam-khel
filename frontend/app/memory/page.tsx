"use client";

import { Card, Empty, Notice, Spinner } from "@/components/Panels";
import { useI18n } from "@/lib/i18n";
import { TACTICS, lab } from "@/lib/labels";
import { useFetch } from "@/lib/useFetch";

interface Script {
  id: number;
  name: string;
  tactic_sequence: string[];
  phrases: string[];
  seen_count: number;
  seed: boolean;
  last_seen: string;
}

export default function MemoryPage() {
  const { t, lang } = useI18n();
  const { data, error, loading } = useFetch<Script[]>("/api/memory/scripts");
  const learned = (data ?? []).filter((s) => !s.seed);
  const builtin = (data ?? []).filter((s) => s.seed);
  const list = (items: Script[]) => (
    <ul className="space-y-3">
      {items.map((s) => (
        <li key={s.id} className="border-b border-sep pb-3 last:border-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-headline">{s.name}</span>
            <span className="chip">
              {t("memory.seen")} {s.seen_count}
            </span>
          </div>
          <ol className="mt-2 flex flex-wrap gap-1.5" aria-label="Tactic order">
            {s.tactic_sequence.map((x, i) => (
              <li key={x} className="rounded-full bg-raised px-2.5 py-0.5 text-footnote">
                {i + 1}. {lab(TACTICS, x, lang)}
              </li>
            ))}
          </ol>
          {s.phrases.length > 0 && <p className="mt-2 text-footnote text-label3">“{s.phrases.slice(0, 3).join("” · “")}”</p>}
        </li>
      ))}
    </ul>
  );
  return (
    <div className="space-y-4">
      <h1 className="text-title1">{t("memory.title")}</h1>
      <p className="text-callout text-label2">{t("memory.sub")}</p>
      {loading && <Spinner label={t("common.loading")} />}
      {error && <Notice tone="error">{error}</Notice>}
      <Card title={t("memory.learned")}>{learned.length ? list(learned) : <Empty>{t("incidents.empty")}</Empty>}</Card>
      <Card title={t("memory.builtin")}>{list(builtin)}</Card>
    </div>
  );
}
