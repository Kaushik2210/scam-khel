"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Icon } from "@/components/Icon";
import { Card, EvidencePanel, Notice, SimBanner, Spinner, TacticTimeline, Transcript, VerificationPanel } from "@/components/Panels";
import { download } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { EvidenceItem, Line, TimelinePoint, Verification } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";

interface Detail {
  id: number;
  session_id: string;
  summary: string;
  risk_peak: number;
  time_wasted_s: number;
  detect_turn: number | null;
  memory_hit_turn: number | null;
  script: string | null;
  simulation: boolean;
  scenario: string | null;
  timeline: { turn: number; stage: string; tactics: string[]; risk: number }[];
  verifications: Verification[];
  transcript: { turn: number; speaker: Line["speaker"]; text: string }[];
  evidence: EvidenceItem[];
}

export default function IncidentPage({ params }: { params: { id: string } }) {
  const { t } = useI18n();
  const { data, error, loading } = useFetch<Detail>(`/api/incidents/${params.id}`);
  const [upTo, setUpTo] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const maxTurn = useMemo(() => Math.max(0, ...(data?.transcript ?? []).map((x) => x.turn)), [data]);
  const shown = upTo ?? maxTurn;
  const lines: Line[] = (data?.transcript ?? []).filter((x) => x.turn <= shown);
  const points: TimelinePoint[] = (data?.timeline ?? [])
    .filter((x) => x.turn <= shown)
    .map((x) => ({ turn: x.turn, score: x.risk, stage: x.stage, tactics: x.tactics }));

  const dl = async (kind: "pdf" | "md") => {
    if (!data) return;
    setErr(null);
    try {
      await download(`/api/sessions/${data.session_id}/complaint.${kind}`, `complaint-draft.${kind}`);
    } catch {
      setErr(t("common.error"));
    }
  };

  return (
    <div className="space-y-4">
      <Link href="/incidents" className="inline-flex min-h-tap items-center text-callout text-tint underline">
        ← {t("incidents.title")}
      </Link>
      {loading && <Spinner label={t("common.loading")} />}
      {error && <Notice tone="error">{error}</Notice>}
      {data && (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-title1">
              #{data.id} {data.scenario ?? ""}
            </h1>
            <span className="chip">{data.risk_peak}/100</span>
            {data.script && <span className="chip">{data.script}</span>}
          </div>
          {data.simulation && <SimBanner />}
          <p className="text-callout text-label2">{data.summary}</p>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn-primary" onClick={() => dl("pdf")}>
              <Icon name="download" /> {t("actions.pdf")}
            </button>
            <button type="button" className="btn-secondary" onClick={() => dl("md")}>
              {t("actions.md")}
            </button>
            <button type="button" className="btn-secondary" onClick={() => download("/api/blocklist.csv", "blocklist.csv")}>
              {t("actions.blocklist")}
            </button>
          </div>
          {err && <Notice tone="error">{err}</Notice>}
          <p className="text-footnote text-label3">{t("common.draft")}</p>

          {maxTurn > 1 && (
            <Card title={t("incidents.replay")}>
              <label className="flex items-center gap-3">
                <span className="text-callout">
                  #{shown} / {maxTurn}
                </span>
                <input
                  type="range"
                  min={1}
                  max={maxTurn}
                  value={shown}
                  onChange={(e) => setUpTo(+e.target.value)}
                  className="h-11 w-full accent-[var(--tint)]"
                  aria-label={t("incidents.replay")}
                />
              </label>
            </Card>
          )}
          <div className="grid gap-4 lg:grid-cols-[3fr_2fr]">
            <Transcript lines={lines} simulation={data.simulation} />
            <div className="space-y-4">
              <TacticTimeline points={points} />
              <EvidencePanel items={data.evidence} />
              <VerificationPanel items={data.verifications} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
