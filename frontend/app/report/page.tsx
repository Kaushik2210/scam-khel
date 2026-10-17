"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { CopyField } from "@/components/CopyField";
import { Icon } from "@/components/Icon";
import { Card, Empty, Notice, Skeleton } from "@/components/Panels";
import { useI18n, type Key } from "@/lib/i18n";
import { useFetch } from "@/lib/useFetch";

interface Row {
  id: number;
  scenario: string | null;
  summary: string;
  created: string;
  risk_peak: number;
}
interface Field {
  label: string;
  value: string;
}
interface Report {
  portal: string;
  helpline: string;
  simulation: boolean;
  note: string;
  groups: { group: string; fields: Field[] }[];
}

const STEP_KEYS: Key[] = ["report.step1", "report.step2", "report.step3", "report.step4", "report.step5", "report.step6"];
const STEPS_STORE = "sk_report_steps";

function loadSteps(id: number | null): boolean[] {
  try {
    const all = JSON.parse(window.localStorage.getItem(STEPS_STORE) ?? "{}") as Record<string, boolean[]>;
    return all[String(id)] ?? STEP_KEYS.map(() => false);
  } catch {
    return STEP_KEYS.map(() => false);
  }
}
function saveSteps(id: number | null, steps: boolean[]) {
  try {
    const all = JSON.parse(window.localStorage.getItem(STEPS_STORE) ?? "{}") as Record<string, boolean[]>;
    all[String(id)] = steps;
    window.localStorage.setItem(STEPS_STORE, JSON.stringify(all));
  } catch {
    /* progress just will not persist */
  }
}

/** Filing assistant. It prepares text and steps; the user logs in, solves the captcha and submits. */
export default function ReportPage() {
  const { t } = useI18n();
  const list = useFetch<Row[]>("/api/incidents");
  const [id, setId] = useState<number | null>(null);
  const [steps, setSteps] = useState<boolean[]>(STEP_KEYS.map(() => false));
  const [txn, setTxn] = useState({ amount: "", date: "", to: "", bank: "", ref: "" });
  const [txnFields, setTxnFields] = useState<Field[]>([]);

  useEffect(() => {
    const fromUrl = Number(new URLSearchParams(window.location.search).get("incident"));
    if (fromUrl) setId(fromUrl);
  }, []);
  useEffect(() => {
    if (id === null && list.data && list.data.length) setId(list.data[0].id);
  }, [list.data, id]);
  useEffect(() => {
    setSteps(loadSteps(id));
    setTxnFields([]);
  }, [id]);

  const report = useFetch<Report>(id ? `/api/incidents/${id}/report-fields` : null);
  const done = steps.filter(Boolean).length;
  const toggle = (i: number) => {
    const next = steps.map((v, j) => (j === i ? !v : v));
    setSteps(next);
    saveSteps(id, next);
  };
  const addTxn = (e: React.FormEvent) => {
    e.preventDefault();
    const f: Field[] = [
      { label: "Amount transferred", value: txn.amount ? `Rs ${txn.amount}` : "" },
      { label: "Date of transaction", value: txn.date },
      { label: "Beneficiary account / UPI", value: txn.to },
      { label: "Beneficiary bank", value: txn.bank },
      { label: "Transaction reference (UTR)", value: txn.ref },
    ].filter((x) => x.value);
    setTxnFields(f);
  };
  const portal = report.data?.portal ?? "https://cybercrime.gov.in";
  const pct = useMemo(() => Math.round((done / STEP_KEYS.length) * 100), [done]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-title1">{t("report.title")}</h1>
        <p className="mt-1 max-w-3xl text-callout text-label2">{t("report.sub")}</p>
      </div>
      <Notice tone="info">{t("report.never")}</Notice>

      {list.loading && <Skeleton rows={2} />}
      {list.error && <Notice tone="error">{list.error}</Notice>}
      {list.data && list.data.length === 0 && (
        <Card title={t("report.choose")}>
          <Empty icon="doc">{t("report.none")}</Empty>
          <div className="flex justify-center gap-2">
            <Link href="/live" className="btn-primary">
              {t("nav.shield")}
            </Link>
            <Link href="/simulate" className="btn-secondary">
              {t("nav.simulate")}
            </Link>
          </div>
        </Card>
      )}

      {list.data && list.data.length > 0 && (
        <label className="block max-w-xl">
          <span className="mb-1 block text-subhead font-semibold">{t("report.choose")}</span>
          <select className="field" value={id ?? ""} onChange={(e) => setId(Number(e.target.value))} data-testid="incident-select">
            {list.data.map((r) => (
              <option key={r.id} value={r.id}>
                #{r.id} · {r.scenario ?? "incident"} · {r.risk_peak}/100 · {new Date(r.created).toLocaleDateString()}
              </option>
            ))}
          </select>
        </label>
      )}

      {report.data?.simulation && <Notice tone="warn">{t("report.simWarn")}</Notice>}

      <div className="grid gap-4 lg:grid-cols-[2fr_3fr]">
        <div className="space-y-4 lg:sticky lg:top-4 lg:self-start">
          <Card title={t("report.steps")} right={<span className="chip">{done}/{STEP_KEYS.length} {t("report.progress")}</span>}>
            <div className="mb-3 h-2 overflow-hidden rounded-full bg-raised" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label={t("report.steps")}>
              <div className="meter-fill h-full bg-ok" style={{ width: `${pct}%` }} />
            </div>
            <ol className="space-y-1">
              {STEP_KEYS.map((k, i) => (
                <li key={k}>
                  <label className="flex min-h-tap cursor-pointer items-start gap-3 rounded-ctl px-2 py-2 hover:bg-raised">
                    <input type="checkbox" className="mt-0.5 h-5 w-5 shrink-0 accent-[var(--tint)]" checked={steps[i]} onChange={() => toggle(i)} />
                    <span className={`text-callout ${steps[i] ? "text-label3 line-through" : ""}`}>
                      <strong className="mr-1">{i + 1}.</strong>
                      {t(k)}
                    </span>
                  </label>
                </li>
              ))}
            </ol>
            <div className="mt-4 flex flex-wrap gap-2">
              <a href="tel:1930" className="btn-danger">
                <Icon name="phone" /> 1930
              </a>
              <a href={portal} target="_blank" rel="noopener noreferrer" className="btn-primary" data-testid="open-portal">
                <Icon name="link" /> {t("report.open")}
              </a>
            </div>
          </Card>

          <Card title={t("report.txn")}>
            <form onSubmit={addTxn} className="space-y-2">
              {(
                [
                  ["amount", "Amount (₹)", "number"],
                  ["date", "Date", "date"],
                  ["to", "Sent to (UPI / account)", "text"],
                  ["bank", "Bank", "text"],
                  ["ref", "Reference (UTR)", "text"],
                ] as const
              ).map(([k, label, type]) => (
                <label key={k} className="block">
                  <span className="mb-0.5 block text-footnote font-semibold text-label2">{label}</span>
                  <input className="field" type={type} value={txn[k]} onChange={(e) => setTxn({ ...txn, [k]: e.target.value })} />
                </label>
              ))}
              <button type="submit" className="btn-secondary w-full">
                {t("report.txnAdd")}
              </button>
            </form>
          </Card>
        </div>

        <div className="space-y-4">
          {report.loading && <Skeleton rows={3} />}
          {report.error && <Notice tone="error">{report.error}</Notice>}
          {report.data &&
            report.data.groups.map((g) => (
              <Card key={g.group} title={g.group}>
                {g.fields.map((f) => (
                  <CopyField key={f.label + f.value} label={f.label} value={f.value} multiline={f.value.length > 80} />
                ))}
              </Card>
            ))}
          {txnFields.length > 0 && (
            <Card title="Transaction details">
              {txnFields.map((f) => (
                <CopyField key={f.label} label={f.label} value={f.value} />
              ))}
            </Card>
          )}
        </div>
      </div>
      <p className="text-footnote text-label3">{t("common.draft")}</p>
    </div>
  );
}
