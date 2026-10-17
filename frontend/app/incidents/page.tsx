"use client";

import Link from "next/link";
import { Notice, Spinner, Empty } from "@/components/Panels";
import { useI18n } from "@/lib/i18n";
import { useFetch } from "@/lib/useFetch";

interface Row {
  id: number;
  summary: string;
  created: string;
  risk_peak: number;
  mode: string;
  scenario: string | null;
  detect_turn: number | null;
  memory_hit_turn: number | null;
}

export default function Incidents() {
  const { t } = useI18n();
  const { data, error, loading, reload } = useFetch<Row[]>("/api/incidents");
  return (
    <div className="space-y-4">
      <h1 className="text-title1">{t("incidents.title")}</h1>
      {loading && <Spinner label={t("common.loading")} />}
      {error && (
        <Notice tone="error">
          {error}{" "}
          <button type="button" className="underline" onClick={reload}>
            {t("common.retry")}
          </button>
        </Notice>
      )}
      {data && data.length === 0 && <Empty>{t("incidents.empty")}</Empty>}
      <ul className="space-y-3">
        {(data ?? []).map((r) => (
          <li key={r.id}>
            <Link href={`/incidents/${r.id}`} className="card block hover:bg-raised">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-headline">#{r.id}</span>
                <span className="chip">{r.scenario ?? r.mode}</span>
                <span className="chip">
                  {r.risk_peak}/100
                </span>
                {r.memory_hit_turn != null && <span className="chip">memory hit @ {r.memory_hit_turn}</span>}
                <span className="ml-auto text-footnote text-label3">{new Date(r.created).toLocaleString()}</span>
              </div>
              <p className="mt-1 text-callout text-label2">{r.summary}</p>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
