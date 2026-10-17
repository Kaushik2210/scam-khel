"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRequireConsent } from "@/components/Consent";
import { Icon } from "@/components/Icon";
import {
  AlertsCard,
  EvidencePanel,
  MemoryCard,
  Notice,
  RiskMeter,
  SimBanner,
  Spinner,
  TacticTimeline,
  Transcript,
  VerificationPanel,
  WastedCard,
} from "@/components/Panels";
import { download } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { Scenario } from "@/lib/types";
import { useFetch } from "@/lib/useFetch";
import { useSession } from "@/lib/useSession";

export default function Simulate() {
  const { t, lang } = useI18n();
  const requireConsent = useRequireConsent();
  const scen = useFetch<Scenario[]>("/api/scenarios");
  const { state, start, sendText, takeover, stop, reset } = useSession();
  const [scenario, setScenario] = useState("digital-arrest-parcel");
  const [manual, setManual] = useState(false);
  const [speed, setSpeed] = useState(2);
  const [reply, setReply] = useState("");
  const [dlError, setDlError] = useState<string | null>(null);

  useEffect(() => {
    if (scen.data && !scen.data.some((s) => s.id === scenario)) setScenario(scen.data[0]?.id ?? scenario);
  }, [scen.data, scenario]);

  const busy = state.status === "connecting" || state.status === "running";
  const onStart = async () => {
    if (!(await requireConsent())) return;
    start({ mode: manual ? "manual" : "honeypot", scenario, language: lang, speed });
  };
  const dl = async (kind: "pdf" | "md") => {
    setDlError(null);
    try {
      await download(`/api/sessions/${state.sessionId}/complaint.${kind}`, `complaint-draft.${kind}`);
    } catch {
      setDlError(t("common.error"));
    }
  };
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!reply.trim()) return;
    sendText(reply.trim());
    setReply("");
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-title1">{t("sim.title")}</h1>
      </div>
      <SimBanner />

      <section className="card grid gap-4 md:grid-cols-[1fr_1fr_auto]" aria-label="Setup">
        <label className="block">
          <span className="mb-1 block text-subhead font-semibold">{t("sim.scenario")}</span>
          <select
            className="field"
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            disabled={busy}
            data-testid="scenario"
          >
            {(scen.data ?? []).map((s) => (
              <option key={s.id} value={s.id}>
                {s.title}
              </option>
            ))}
          </select>
          {scen.error && <span className="text-footnote text-danger">{scen.error}</span>}
        </label>
        <fieldset disabled={busy}>
          <legend className="mb-1 text-subhead font-semibold">{t("sim.mode")}</legend>
          <div className="flex flex-col gap-1">
            {[
              [false, "sim.auto"],
              [true, "sim.manual"],
            ].map(([v, k]) => (
              <label key={String(v)} className="flex min-h-tap items-center gap-2">
                <input type="radio" name="who" checked={manual === v} onChange={() => setManual(v as boolean)} className="h-5 w-5 accent-[var(--tint)]" />
                {t(k as "sim.auto")}
              </label>
            ))}
          </div>
          {!manual && (
            <label className="mt-1 flex items-center gap-2 text-callout">
              {t("sim.speed")}
              <select className="field !w-auto" value={speed} onChange={(e) => setSpeed(+e.target.value)} aria-label={t("sim.speed")}>
                {[1, 2, 4, 8].map((x) => (
                  <option key={x} value={x}>
                    {x}×
                  </option>
                ))}
              </select>
            </label>
          )}
        </fieldset>
        <div className="flex items-end gap-2">
          {!busy ? (
            <button type="button" className="btn-primary" onClick={onStart} data-testid="start">
              <Icon name="play" /> {t("sim.start")}
            </button>
          ) : (
            <>
              {!manual && (
                <button type="button" className="btn-secondary" onClick={takeover}>
                  {t("sim.takeover")}
                </button>
              )}
              <button type="button" className="btn-secondary" onClick={stop}>
                <Icon name="stop" /> {t("sim.stop")}
              </button>
            </>
          )}
        </div>
      </section>

      {state.budgetNotice && <Notice tone="warn">{state.replay ? t("state.budget") : state.budgetNotice}</Notice>}
      {state.replay && <Notice>{t("state.replay")}</Notice>}
      {state.status === "error" && (
        <Notice tone="error">
          {t("state.error")} {state.error && state.error !== "connection" ? `(${state.error})` : ""}{" "}
          <button type="button" className="btn-plain !min-h-0 !px-1 underline" onClick={reset}>
            {t("common.retry")}
          </button>
        </Notice>
      )}
      {state.status === "connecting" && <Spinner label={t("state.connecting")} />}

      <div className="grid gap-4 lg:grid-cols-[3fr_2fr]">
        <div className="space-y-4">
          <Transcript lines={state.transcript} simulation thinking={busy} />
          {manual && busy && (
            <form onSubmit={submit} className="card flex gap-2" aria-label={t("sim.reply")}>
              <input
                className="field"
                value={reply}
                onChange={(e) => setReply(e.target.value)}
                placeholder={t("sim.reply")}
                aria-label={t("sim.reply")}
                maxLength={1000}
                data-testid="reply"
              />
              <button type="submit" className="btn-primary">
                {t("common.send")}
              </button>
            </form>
          )}
          {state.status === "ended" && (
            <section className="card space-y-3" aria-label={t("sim.finished")}>
              <h2 className="text-headline">{t("sim.finished")}</h2>
              <div className="flex flex-wrap gap-2">
                {state.summary?.incident_id && !state.replay && (
                  <>
                    <button type="button" className="btn-primary" onClick={() => dl("pdf")} data-testid="dl-pdf">
                      <Icon name="download" /> {t("actions.pdf")}
                    </button>
                    <button type="button" className="btn-secondary" onClick={() => dl("md")}>
                      {t("actions.md")}
                    </button>
                    <Link className="btn-secondary" href={`/incidents/${state.summary.incident_id}`}>
                      {t("actions.incident")}
                    </Link>
                  </>
                )}
                <Link className="btn-danger" href="/parent#panic">
                  {t("actions.panic")}
                </Link>
              </div>
              {dlError && <Notice tone="error">{dlError}</Notice>}
              <p className="text-footnote text-label3">{t("common.draft")}</p>
            </section>
          )}
        </div>
        <div className="space-y-4">
          <RiskMeter risk={state.risk} />
          <MemoryCard hit={state.memoryHit} />
          {!manual && <WastedCard seconds={state.timeWasted} turns={state.engaged} />}
          <EvidencePanel items={state.evidence} />
          <VerificationPanel items={state.verifications} />
          <TacticTimeline points={state.timeline} />
          <AlertsCard alerts={state.alerts} />
        </div>
      </div>
    </div>
  );
}
