"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRequireConsent } from "@/components/Consent";
import { Icon } from "@/components/Icon";
import { ListenPanel } from "@/components/ListenPanel";
import { MicButton } from "@/components/MicButton";
import {
  AlertsCard,
  EvidencePanel,
  MemoryCard,
  Notice,
  RiskMeter,
  Spinner,
  StatusPill,
  TacticTimeline,
  Transcript,
  Verdict,
} from "@/components/Panels";
import { download } from "@/lib/api";
import { EXAMPLES } from "@/lib/examples";
import { useI18n, type Key } from "@/lib/i18n";
import { useSession } from "@/lib/useSession";

type Tab = "paste" | "listen";

export default function Live() {
  const { t, lang } = useI18n();
  const requireConsent = useRequireConsent();
  const { state, start, sendText, stop, reset } = useSession();
  const [tab, setTab] = useState<Tab>("paste");
  const [text, setText] = useState("");
  const [pending, setPending] = useState<string[]>([]);
  const active = state.status === "running" || state.status === "connecting";
  const high = state.risk && (state.risk.level === "high" || state.risk.level === "critical");

  const ensureSession = useCallback(async () => {
    if (state.status === "running" || state.status === "connecting") return true;
    if (!(await requireConsent())) return false;
    await start({ mode: "shield", scenario: "shield", language: lang });
    return true;
  }, [state.status, requireConsent, start, lang]);

  const analyze = async () => {
    const lines = text
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
    if (!lines.length) return;
    if (!(await ensureSession())) return;
    setText("");
    setPending((p) => [...p, ...lines]);
  };
  const onListenLine = useCallback((line: string) => setPending((p) => [...p, line]), []);

  // flush queued lines once the socket is open
  useEffect(() => {
    if (state.status === "running" && pending.length) {
      pending.forEach((l) => sendText(l, "caller"));
      setPending([]);
    }
  }, [state.status, pending, sendText]);

  const tabs: { id: Tab; label: Key; icon: string }[] = [
    { id: "paste", label: "live.tab.paste", icon: "doc" },
    { id: "listen", label: "live.tab.listen", icon: "mic" },
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-title1">{t("live.title")}</h1>
        <StatusPill status={state.status} />
      </div>
      <p className="max-w-3xl text-callout text-label2">{t("live.hint")}</p>

      <div role="tablist" aria-label={t("live.title")} className="inline-flex rounded-ctl bg-raised p-1">
        {tabs.map((x) => (
          <button
            key={x.id}
            type="button"
            role="tab"
            id={`tab-${x.id}`}
            aria-selected={tab === x.id}
            aria-controls={`panel-${x.id}`}
            data-testid={`tab-${x.id}`}
            onClick={() => setTab(x.id)}
            className={`flex min-h-[40px] items-center gap-2 rounded-[9px] px-4 text-callout font-semibold ${
              tab === x.id ? "bg-surface text-label shadow" : "text-label2"
            }`}
          >
            <Icon name={x.icon} size={18} /> {t(x.label)}
          </button>
        ))}
      </div>

      {tab === "paste" ? (
        <section id="panel-paste" role="tabpanel" aria-labelledby="tab-paste" className="card space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-subhead font-semibold text-label2">{t("live.examples")}:</span>
            {EXAMPLES.map((ex) => (
              <button
                key={ex.id}
                type="button"
                className="chip !min-h-[36px] cursor-pointer !px-4 !text-callout hover:bg-sep"
                onClick={() => setText(ex.text[lang])}
                data-testid={`example-${ex.id}`}
              >
                {t(`live.ex.${ex.id}` as Key)}
              </button>
            ))}
          </div>
          <label htmlFor="paste" className="sr-only">
            {t("live.title")}
          </label>
          <textarea
            id="paste"
            className="field min-h-[9rem] py-3"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder={t("live.placeholder")}
            maxLength={8000}
            data-testid="paste"
          />
          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn-primary !min-h-[52px] !px-7" onClick={analyze} disabled={!text.trim()} data-testid="analyze">
              <Icon name="shield" /> {state.status === "running" ? t("live.add") : t("live.analyze")}
            </button>
            <MicButton onText={(x) => setText((p) => (p ? `${p}\n` : "") + x)} />
          </div>
        </section>
      ) : (
        <div id="panel-listen" role="tabpanel" aria-labelledby="tab-listen">
          <ListenPanel onLine={onListenLine} onStarted={ensureSession} />
        </div>
      )}

      <div className="flex flex-wrap gap-2">
        {active && (
          <button type="button" className="btn-secondary" onClick={stop}>
            <Icon name="stop" /> {t("sim.stop")}
          </button>
        )}
        {state.status !== "idle" && (
          <button type="button" className="btn-plain" onClick={reset}>
            {t("live.reset")}
          </button>
        )}
      </div>

      {state.status === "connecting" && <Spinner label={t("state.connecting")} />}
      {state.status === "error" && <Notice tone="error">{t("state.error")}</Notice>}
      {state.risk && <Verdict level={state.risk.level} summary={state.risk.summary} />}
      {tab === "listen" && high && (
        <div className="rounded-card bg-[var(--crit-fill)] p-4 text-center text-title2 text-white" role="alert">
          {t("listen.alert")}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[3fr_2fr]">
        <div className="order-first space-y-4 lg:order-last lg:sticky lg:top-4 lg:self-start">
          <RiskMeter risk={state.risk} />
          <MemoryCard hit={state.memoryHit} />
        </div>
        <div className="space-y-4">
          <Transcript lines={state.transcript} simulation={false} />
          {high && (
            <div className="flex flex-wrap gap-2">
              <Link className="btn-danger" href="/parent#panic">
                {t("actions.panic")}
              </Link>
              {state.status === "ended" && state.sessionId && state.summary?.incident_id && (
                <>
                  <Link className="btn-primary" href={`/report?incident=${state.summary.incident_id}`} data-testid="to-report">
                    <Icon name="doc" /> {t("nav.fileReport")}
                  </Link>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => download(`/api/sessions/${state.sessionId}/complaint.pdf`, "complaint-draft.pdf")}
                  >
                    <Icon name="download" /> {t("actions.pdf")}
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <EvidencePanel items={state.evidence} />
        <TacticTimeline points={state.timeline} />
        <AlertsCard alerts={state.alerts} />
      </div>
    </div>
  );
}
