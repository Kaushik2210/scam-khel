"use client";

import { useEffect, useRef } from "react";
import { Icon } from "./Icon";
import { useI18n, type Key } from "@/lib/i18n";
import { EVIDENCE_TYPES, STAGES, TACTICS, fmtDuration, lab } from "@/lib/labels";
import type { EvidenceItem, Level, Line, MemoryHit, Risk, TimelinePoint, Verification } from "@/lib/types";
import type { AlertNote, Status } from "@/lib/useSession";

const LEVEL_STYLE: Record<Level, { color: string; box: string; icon: string }> = {
  low: { color: "var(--ok)", box: "bg-ok-bg", icon: "check" },
  caution: { color: "var(--warn)", box: "bg-warn-bg", icon: "info" },
  high: { color: "var(--danger)", box: "bg-danger-bg", icon: "alert" },
  critical: { color: "var(--crit)", box: "bg-crit-bg", icon: "alert" },
};
const STAGE_ORDER = ["contact", "accusation", "isolation", "verification", "payment"];

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
      <span className="mt-0.5 shrink-0">
        <Icon name={tone === "info" ? "info" : "alert"} />
      </span>
      <div>{children}</div>
    </div>
  );
}

export function Empty({ children, icon = "info" }: { children: React.ReactNode; icon?: string }) {
  return (
    <div className="flex flex-col items-center gap-2 py-6 text-center text-callout text-label3">
      <span className="text-label3 opacity-70">
        <Icon name={icon} size={28} />
      </span>
      <p className="max-w-xs">{children}</p>
    </div>
  );
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

export function Skeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3" aria-hidden="true">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="skeleton h-16 rounded-card" />
      ))}
    </div>
  );
}

export function StatusPill({ status }: { status: Status }) {
  const { t } = useI18n();
  const tone: Record<Status, string> = {
    idle: "bg-raised text-label2",
    connecting: "bg-warn-bg text-label",
    running: "bg-ok-bg text-label",
    ended: "bg-raised text-label",
    error: "bg-crit-bg text-label",
  };
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-footnote font-semibold ${tone[status]}`} role="status">
      <span
        className={`h-2 w-2 rounded-full ${status === "running" ? "bg-ok motion-safe:animate-pulse" : status === "error" ? "bg-crit" : "bg-label3"}`}
        aria-hidden="true"
      />
      {t(`status.${status}` as Key)}
    </span>
  );
}

export function Card({
  title,
  children,
  right,
  className = "",
}: {
  title: string;
  children: React.ReactNode;
  right?: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`card ${className}`} aria-label={title}>
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-headline">{title}</h2>
        {right}
      </div>
      {children}
    </section>
  );
}

/** Semicircular risk gauge. Colour AND text AND icon convey the level (never colour alone). */
export function RiskMeter({ risk }: { risk: Risk | null }) {
  const { t, lang } = useI18n();
  const score = risk?.score ?? 0;
  const level: Level = risk?.level ?? "low";
  const st = LEVEL_STYLE[level];
  const R = 80;
  const C = Math.PI * R;
  const last = useRef<Level | null>(null);
  const announce = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (risk && last.current !== risk.level && announce.current) {
      announce.current.textContent = `${t("panel.risk")}: ${t(`risk.${risk.level}` as Key)}, ${risk.score} ${t("risk.of")}`;
    }
    last.current = risk?.level ?? null;
  }, [risk, t]);
  const tick = (m: number) => {
    const a = Math.PI * (1 - m / 100);
    return { x1: 100 + (R - 11) * Math.cos(a), y1: 100 - (R - 11) * Math.sin(a), x2: 100 + (R + 11) * Math.cos(a), y2: 100 - (R + 11) * Math.sin(a) };
  };
  const stageIdx = risk ? STAGE_ORDER.indexOf(risk.stage) : -1;
  return (
    <Card title={t("panel.risk")}>
      <div ref={announce} className="sr-only" aria-live="polite" />
      <div className={`rounded-ctl p-4 ${st.box}`}>
        <svg
          viewBox="0 0 200 118"
          className="mx-auto w-full max-w-[300px]"
          role="meter"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={score}
          aria-valuetext={`${t(`risk.${level}` as Key)}, ${score}`}
          aria-label={t("panel.risk")}
        >
          <path d="M20 100 A80 80 0 0 1 180 100" fill="none" stroke="var(--raised)" strokeWidth="14" strokeLinecap="round" />
          <path
            d="M20 100 A80 80 0 0 1 180 100"
            fill="none"
            stroke={st.color}
            strokeWidth="14"
            strokeLinecap="round"
            strokeDasharray={C}
            strokeDashoffset={C * (1 - score / 100)}
            className="gauge-fill"
          />
          {[40, 70, 85].map((m) => {
            const p = tick(m);
            return <line key={m} {...p} stroke="var(--label-3)" strokeWidth="1.5" />;
          })}
          <text x="100" y="92" textAnchor="middle" fontSize="40" fontWeight="700" fill="var(--label)" data-testid="risk-score">
            {score}
          </text>
          <text x="100" y="112" textAnchor="middle" fontSize="12" fill="var(--label-2)">
            {t("risk.of")}
          </text>
        </svg>
        <div className="mt-1 flex items-center justify-center gap-2 text-title2" data-testid="risk-level" data-level={level}>
          <Icon name={st.icon} size={24} />
          {t(`risk.${level}` as Key)}
        </div>
        {risk && <p className="mt-2 text-center text-callout">{risk.summary}</p>}
      </div>

      <div className="mt-4">
        <h3 className="mb-2 text-subhead font-semibold text-label2">{t("panel.stage")}</h3>
        <ol className="flex items-center" aria-label={t("panel.stage")}>
          {STAGE_ORDER.map((s, i) => {
            const done = i < stageIdx;
            const now = i === stageIdx;
            return (
              <li key={s} className="flex flex-1 flex-col items-center gap-1" aria-current={now ? "step" : undefined}>
                <span
                  className={`flex h-7 w-7 items-center justify-center rounded-full text-caption font-bold ${
                    now ? "bg-tint text-tint-on" : done ? "bg-raised text-label" : "border border-sep text-label3"
                  }`}
                >
                  {done ? "✓" : i + 1}
                </span>
                <span className={`text-center text-caption leading-tight ${now ? "font-semibold text-label" : "text-label3"}`}>
                  {lab(STAGES, s, lang)}
                </span>
              </li>
            );
          })}
        </ol>
      </div>

      {risk && risk.tactics.length > 0 && (
        <div className="mt-4">
          <h3 className="mb-2 text-subhead font-semibold text-label2">{t("panel.currentTactics")}</h3>
          <ul className="flex flex-wrap gap-1.5">
            {risk.tactics.map((x) => (
              <li key={x} className="rounded-full bg-raised px-2.5 py-1 text-footnote">
                {lab(TACTICS, x, lang)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {risk && risk.what_to_do.length > 0 && (
        <div className="mt-4 rounded-ctl border border-sep p-3">
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
        <Empty icon="clock">{t("state.idle")}</Empty>
      ) : (
        <ol className="relative space-y-3 border-l border-sep pl-4">
          {points.map((p, i) => {
            const prev = points[i - 1]?.tactics ?? [];
            const fresh = p.tactics.filter((x) => !prev.includes(x));
            // collapse turns that add nothing new (keep the first and the latest)
            if (fresh.length === 0 && i !== 0 && i !== points.length - 1) return null;
            return (
              <li key={p.turn} className="relative text-callout">
                <span className="absolute -left-[1.4rem] top-1.5 h-2.5 w-2.5 rounded-full bg-tint" aria-hidden="true" />
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold">#{p.turn}</span>
                  <span className="rounded-full bg-raised px-2 py-0.5 text-footnote font-semibold">{p.score}</span>
                  <span className="text-footnote text-label3">{lab(STAGES, p.stage, lang)}</span>
                </div>
                {fresh.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {fresh.map((x) => (
                      <span key={x} className="rounded-full bg-danger-bg px-2 py-0.5 text-footnote">
                        {lab(TACTICS, x, lang)}
                      </span>
                    ))}
                  </div>
                )}
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
        <Empty icon="phone">{thinking ? t("sim.waiting") : t("state.idle")}</Empty>
      ) : (
        <ul className="max-h-[32rem] space-y-3 overflow-y-auto pr-1" aria-live="off" data-testid="transcript">
          {lines.map((l, i) => {
            const caller = l.speaker === "scammer" || l.speaker === "caller";
            return (
              <li key={i} className={`anim-in flex items-end gap-2 ${caller ? "justify-start" : "flex-row-reverse"}`}>
                <span
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${caller ? "bg-crit-bg" : "bg-raised"}`}
                  aria-hidden="true"
                >
                  <Icon name={caller ? "phone" : "users"} size={16} />
                </span>
                <div className={`max-w-[85%] rounded-[18px] px-3.5 py-2 ${caller ? "rounded-bl-md bg-crit-bg" : "rounded-br-md bg-raised"}`}>
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
        <Empty icon="doc">{t("state.noEvidence")}</Empty>
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
        <Empty icon="globe">{t("state.noVerify")}</Empty>
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
        <Empty icon="brain">{t("state.noMemory")}</Empty>
      )}
    </Card>
  );
}

export function AlertsCard({ alerts }: { alerts: AlertNote[] }) {
  const { t } = useI18n();
  return (
    <Card title={t("panel.alerts")}>
      {alerts.length === 0 ? (
        <Empty icon="users">{t("state.noAlerts")}</Empty>
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

/** Big plain-language verdict used by Shield and Parent view. */
export function Verdict({ level, summary }: { level: Level; summary: string }) {
  const { t } = useI18n();
  const st = LEVEL_STYLE[level];
  const title = level === "high" || level === "critical" ? t("verdict.scam") : level === "caution" ? t("verdict.caution") : t("verdict.ok");
  return (
    <div className={`anim-in flex items-start gap-3 rounded-card p-4 ${st.box}`} role="status" data-testid="verdict" data-level={level}>
      <span style={{ color: st.color }} className="mt-0.5 shrink-0">
        <Icon name={st.icon} size={28} />
      </span>
      <div>
        <p className="text-title2">{title}</p>
        <p className="mt-1 text-callout text-label2">{summary}</p>
      </div>
    </div>
  );
}
