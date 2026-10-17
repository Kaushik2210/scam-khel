"use client";

import { useEffect, useRef } from "react";
import { Icon } from "./Icon";
import { useI18n, type Key } from "@/lib/i18n";
import { EVIDENCE_TYPES, STAGES, TACTICS, fmtDuration, lab } from "@/lib/labels";
import type { EvidenceItem, Level, Line, MemoryHit, Risk, TimelinePoint, Verification } from "@/lib/types";
import type { AlertNote } from "@/lib/useSession";

const LEVEL_STYLE: Record<Level, { bar: string; box: string; icon: string }> = {
  low: { bar: "bg-ok", box: "bg-ok-bg", icon: "check" },
  caution: { bar: "bg-warn", box: "bg-warn-bg", icon: "info" },
  high: { bar: "bg-danger", box: "bg-danger-bg", icon: "alert" },
  critical: { bar: "bg-crit", box: "bg-crit-bg", icon: "alert" },
};

export function SimBadge() {
  const { t } = useI18n();
  return <span className="sim-badge">{t("sim.badge")}</span>;
}

export function SimBanner() {
  const { t } = useI18n();
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-card border border-warn bg-warn-bg p-3" role="note">
      <SimBadge />
      <p className="text-callout text-label">{t("sim.note")}</p>
    </div>
  );
}

export function Notice({ tone = "info", children }: { tone?: "info" | "warn" | "error"; children: React.ReactNode }) {
  const cls = tone === "error" ? "bg-crit-bg" : tone === "warn" ? "bg-warn-bg" : "bg-raised";
  return (
    <div className={`flex gap-3 rounded-card p-3 text-callout ${cls}`} role={tone === "error" ? "alert" : "status"}>
      <Icon name={tone === "info" ? "info" : "alert"} />
      <div>{children}</div>
    </div>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <p className="py-4 text-center text-callout text-label3">{children}</p>;
}

export function Spinner({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 py-4 text-callout text-label2" role="status">
      <span
        className="inline-block h-5 w-5 rounded-full border-2 border-sep border-t-tint motion-safe:animate-spin"
        aria-hidden="true"
      />
      {label}
    </div>
  );
}

export function Card({ title, children, right }: { title: string; children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <section className="card" aria-label={title}>
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-headline">{title}</h2>
        {right}
      </div>
      {children}
    </section>
  );
}

export function RiskMeter({ risk }: { risk: Risk | null }) {
  const { t, lang } = useI18n();
  const score = risk?.score ?? 0;
  const level: Level = risk?.level ?? "low";
  const st = LEVEL_STYLE[level];
  const last = useRef<Level | null>(null);
  const announce = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (risk && last.current !== risk.level && announce.current) {
      announce.current.textContent = `${t("panel.risk")}: ${t(`risk.${risk.level}` as Key)}, ${risk.score} ${t("risk.of")}`;
    }
    last.current = risk?.level ?? null;
  }, [risk, t]);
  return (
    <Card title={t("panel.risk")}>
      <div ref={announce} className="sr-only" aria-live="polite" />
      <div className={`rounded-ctl p-4 ${st.box}`}>
        <div className="flex items-center gap-3">
          <Icon name={st.icon} size={28} />
          <div>
            <div className="text-large leading-none" data-testid="risk-score">
              {score}
            </div>
            <div className="text-callout text-label2">{t("risk.of")}</div>
          </div>
          <div className="ml-auto text-title2" data-testid="risk-level" data-level={level}>
            {t(`risk.${level}` as Key)}
          </div>
        </div>
        <div
          className="relative mt-4 h-3 overflow-hidden rounded-full bg-raised"
          role="meter"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={score}
          aria-valuetext={`${t(`risk.${level}` as Key)}, ${score}`}
          aria-label={t("panel.risk")}
        >
          <div className={`meter-fill h-full ${st.bar}`} style={{ width: `${score}%` }} />
          {[40, 70, 85].map((m) => (
            <span key={m} className="absolute top-0 h-full w-px bg-label3" style={{ left: `${m}%` }} aria-hidden="true" />
          ))}
        </div>
        {risk && <p className="mt-3 text-callout">{risk.summary}</p>}
        {risk && (
          <p className="mt-1 text-footnote text-label2">
            {lab(STAGES, risk.stage, lang)}
          </p>
        )}
      </div>
      {risk && risk.what_to_do.length > 0 && (
        <div className="mt-3">
          <h3 className="mb-1 text-subhead font-semibold">{t("risk.whatToDo")}</h3>
          <ol className="list-decimal space-y-1 pl-5 text-callout">
            {risk.what_to_do.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ol>
        </div>
      )}
    </Card>
  );
}

export function TacticTimeline({ points }: { points: TimelinePoint[] }) {
  const { t, lang } = useI18n();
  return (
    <Card title={t("panel.timeline")}>
      {points.length === 0 ? (
        <Empty>{t("state.idle")}</Empty>
      ) : (
        <ol className="space-y-2">
          {points.map((p, i) => {
            const prev = points[i - 1]?.tactics ?? [];
            const fresh = p.tactics.filter((x) => !prev.includes(x));
            return (
              <li key={p.turn} className="flex flex-wrap items-center gap-2 text-callout">
                <span className="chip">#{p.turn}</span>
                <span className="font-semibold">{p.score}</span>
                <span className="text-label3">{lab(STAGES, p.stage, lang)}</span>
                {fresh.map((x) => (
                  <span key={x} className="rounded-full bg-danger-bg px-2 py-0.5 text-footnote">
                    {lab(TACTICS, x, lang)}
                  </span>
                ))}
              </li>
            );
          })}
        </ol>
      )}
    </Card>
  );
}

export function Transcript({ lines, simulation, thinking }: { lines: Line[]; simulation: boolean; thinking?: boolean }) {
  const { t } = useI18n();
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    end.current?.scrollIntoView?.({ block: "nearest" });
  }, [lines.length]);
  const who = (s: Line["speaker"]) =>
    s === "scammer" || s === "caller" ? (simulation ? "Caller (SIMULATION)" : "Caller") : s === "persona" ? "Decoy" : "You";
  return (
    <Card title={t("panel.transcript")} right={simulation ? <SimBadge /> : null}>
      {lines.length === 0 ? (
        <Empty>{thinking ? t("sim.waiting") : t("state.idle")}</Empty>
      ) : (
        <ul className="max-h-[28rem] space-y-3 overflow-y-auto pr-1" aria-live="off" data-testid="transcript">
          {lines.map((l, i) => {
            const caller = l.speaker === "scammer" || l.speaker === "caller";
            return (
              <li key={i} className={`flex ${caller ? "justify-start" : "justify-end"}`}>
                <div className={`max-w-[88%] rounded-card px-3 py-2 ${caller ? "bg-crit-bg" : "bg-raised"}`}>
                  <div className="text-caption font-semibold text-label2">{who(l.speaker)}</div>
                  <div className="text-body">{l.text}</div>
                </div>
              </li>
            );
          })}
          <div ref={end} />
        </ul>
      )}
    </Card>
  );
}

export function EvidencePanel({ items }: { items: EvidenceItem[] }) {
  const { t, lang } = useI18n();
  return (
    <Card title={t("panel.evidence")} right={<span className="chip">{items.length}</span>}>
      {items.length === 0 ? (
        <Empty>{t("state.noEvidence")}</Empty>
      ) : (
        <dl className="space-y-2" data-testid="evidence">
          {items.map((e) => (
            <div key={`${e.type}:${e.value}`} className="anim-in flex items-baseline justify-between gap-3 border-b border-sep pb-2 last:border-0">
              <dt className="text-footnote text-label2">{lab(EVIDENCE_TYPES, e.type, lang)}</dt>
              <dd className="break-all text-right font-mono text-callout">
                {e.value}
                <span className="ml-2 text-caption text-label3">{Math.round(e.confidence * 100)}%</span>
              </dd>
            </div>
          ))}
        </dl>
      )}
    </Card>
  );
}

export function VerificationPanel({ items }: { items: Verification[] }) {
  const { t } = useI18n();
  return (
    <Card title={t("panel.verification")}>
      {items.length === 0 ? (
        <Empty>{t("state.noVerify")}</Empty>
      ) : (
        <ul className="space-y-3" data-testid="verification">
          {items.map((v, i) => (
            <li key={i} className="text-callout">
              <div className="flex flex-wrap items-center gap-2">
                <span className="chip">{v.kind.replace("_", " ")}</span>
                <span className="break-all text-footnote text-label2">{v.query}</span>
              </div>
              {v.status === "unavailable" && <p className="mt-1 text-label2">{t("verify.unavailable")}</p>}
              {v.status === "no_results" && <p className="mt-1 text-label2">{t("verify.noReports")}</p>}
              {v.sources.slice(0, 3).map((s) => (
                <a key={s.url} href={s.url} target="_blank" rel="noopener noreferrer" className="mt-1 block text-tint underline">
                  {s.title || s.url}
                </a>
              ))}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export function MemoryCard({ hit }: { hit: MemoryHit | null }) {
  const { t } = useI18n();
  return (
    <Card title={t("panel.memory")}>
      {hit ? (
        <div className="anim-in rounded-ctl bg-ok-bg p-3" data-testid="memory-hit">
          <div className="flex items-start gap-2">
            <Icon name="brain" />
            <p className="text-body font-semibold">{hit.banner}</p>
          </div>
          <p className="mt-1 text-footnote text-label2">
            {hit.script} · {t("memory.seen")} {hit.seen_count}
          </p>
        </div>
      ) : (
        <Empty>{t("state.noMemory")}</Empty>
      )}
    </Card>
  );
}

export function AlertsCard({ alerts }: { alerts: AlertNote[] }) {
  const { t } = useI18n();
  return (
    <Card title={t("panel.alerts")}>
      {alerts.length === 0 ? (
        <Empty>{t("state.noAlerts")}</Empty>
      ) : (
        <ul className="space-y-1 text-callout">
          {alerts.map((a, i) => (
            <li key={i}>
              {a.level}: {a.sent > 0 ? `sent to ${a.sent}` : (a.skipped ?? "not sent").replace("_", " ")}
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export function WastedCard({ seconds, turns }: { seconds: number; turns: number }) {
  const { t } = useI18n();
  return (
    <Card title={t("panel.wasted")}>
      <div className="flex items-baseline gap-3">
        <span className="text-large" data-testid="time-wasted">
          {fmtDuration(seconds)}
        </span>
        <span className="text-callout text-label2">
          {turns} {t("panel.engaged")}
        </span>
      </div>
    </Card>
  );
}
