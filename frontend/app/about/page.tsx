"use client";

import { Card } from "@/components/Panels";
import { useI18n } from "@/lib/i18n";

const PRIVACY = [
  "Personal numbers (Aadhaar, PAN, card, OTP, phone) are masked before any model sees the text.",
  "Transcripts are encrypted at rest and deleted after 30 days. No audio is stored.",
  "You can delete everything from the More page at any time.",
  "No trackers, no ads, no third-party analytics.",
  "The decoy persona only ever uses fictional details and never agrees to pay, install or click.",
];
const LIMITS = [
  "It does not intercept real calls. The honeypot talks to a built-in simulated scammer only.",
  "Complaints are drafts. You review and file them yourself at cybercrime.gov.in; call 1930 if money was sent.",
  "Detection is rules plus Nemotron tagging and can be wrong. Treat it as a second opinion, not a verdict.",
  "“No public reports found” from the web check does not mean a number or account is safe.",
  "Voice input uses the browser's speech features, which are not NVIDIA models.",
  "Built for a hackathon demo; fictional agencies are always labelled (SIMULATION).",
];

export default function About() {
  const { t } = useI18n();
  return (
    <div className="space-y-4">
      <h1 className="text-title1">{t("about.title")}</h1>

      <Card title="Architecture">
        <svg viewBox="0 0 640 150" role="img" aria-label="Pipeline: call text to sanitizer, tagger, risk engine, then persona, evidence, alerts and complaint" className="w-full">
          {[
            ["Call text", 10],
            ["Mask PII", 120],
            ["Tag (fast)", 230],
            ["Risk + memory", 340],
            ["Persona (mid)", 450],
          ].map(([label, x], i) => (
            <g key={label as string}>
              <rect x={x as number} y="10" width="100" height="44" rx="10" fill="var(--raised)" stroke="var(--separator)" />
              <text x={(x as number) + 50} y="37" textAnchor="middle" fill="var(--label)" fontSize="12">
                {label}
              </text>
              {i < 4 && <path d={`M${(x as number) + 100} 32 h20`} stroke="var(--label-3)" strokeWidth="1.5" />}
            </g>
          ))}
          {[
            ["Evidence + Tavily", 120],
            ["Family alert", 250],
            ["Complaint (deep)", 380],
          ].map(([label, x]) => (
            <g key={label as string}>
              <path d={`M390 54 L${(x as number) + 55} 96`} stroke="var(--label-3)" strokeWidth="1.2" fill="none" />
              <rect x={x as number} y="96" width="120" height="44" rx="10" fill="var(--raised)" stroke="var(--separator)" />
              <text x={(x as number) + 60} y="123" textAnchor="middle" fill="var(--label)" fontSize="12">
                {label}
              </text>
            </g>
          ))}
        </svg>
      </Card>

      <Card title={t("about.tiers")}>
        <ul className="space-y-2 text-body">
          <li><strong>Fast.</strong> {t("about.fast")}</li>
          <li><strong>Mid.</strong> {t("about.mid")}</li>
          <li><strong>Deep.</strong> {t("about.deep")}</li>
          <li>{t("about.tavily")}</li>
        </ul>
        <p className="mt-3 text-callout text-label2">
          All model calls go to Nebius Token Factory using NVIDIA Nemotron models; model IDs are configured per tier.
        </p>
      </Card>
      <Card title={t("about.privacy")}>
        <ul className="list-disc space-y-1 pl-5 text-callout">{PRIVACY.map((x) => <li key={x}>{x}</li>)}</ul>
      </Card>
      <Card title={t("about.limits")}>
        <ul className="list-disc space-y-1 pl-5 text-callout">{LIMITS.map((x) => <li key={x}>{x}</li>)}</ul>
      </Card>
    </div>
  );
}
