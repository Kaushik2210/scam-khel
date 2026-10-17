"use client";

import Link from "next/link";
import { useState } from "react";
import { Icon } from "@/components/Icon";
import { Card, Notice } from "@/components/Panels";
import { Sheet } from "@/components/Sheet";
import { api, ApiError, revokeConsent } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useFetch } from "@/lib/useFetch";

interface Models {
  provider: string;
  mode: string;
  structured_mode: string;
  tiers: Record<string, { model: string | null; does: string }>;
  note: string | null;
}

export default function More() {
  const { t } = useI18n();
  const models = useFetch<Models>("/api/models/status");
  const [confirm, setConfirm] = useState(false);
  const [done, setDone] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const wipe = async () => {
    try {
      await api("/api/me/data", { method: "DELETE" });
      revokeConsent();
      setDone(true);
      setErr(null);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : t("common.error"));
    }
    setConfirm(false);
  };
  const links = [
    ["/report", "nav.fileReport", "doc"],
    ["/parent", "nav.parent", "phone"],
    ["/family", "nav.family", "users"],
    ["/memory", "nav.memory", "brain"],
    ["/about", "nav.about", "info"],
  ] as const;
  return (
    <div className="space-y-4">
      <h1 className="text-title1">{t("more.title")}</h1>
      <ul className="grid gap-3 sm:grid-cols-2">
        {links.map(([href, key, icon]) => (
          <li key={href}>
            <Link href={href} className="card flex min-h-tapxl items-center gap-3 text-headline hover:bg-raised">
              <Icon name={icon} size={24} /> {t(key)}
            </Link>
          </li>
        ))}
      </ul>

      <Card title={t("more.models")}>
        {models.data && (
          <div className="space-y-2 text-callout">
            <p>
              {models.data.provider} · <span className="chip">{models.data.mode}</span>
            </p>
            {Object.entries(models.data.tiers).map(([tier, v]) => (
              <p key={tier}>
                <strong>{tier}</strong>: <code className="font-mono">{v.model ?? "not set"}</code>{" "}
                <span className="text-label3">{v.does}</span>
              </p>
            ))}
            {models.data.note && <Notice tone="warn">{models.data.note}</Notice>}
          </div>
        )}
        {models.error && <Notice tone="error">{models.error}</Notice>}
      </Card>

      <Card title={t("more.delete")}>
        {done && <Notice>{t("more.deleted")}</Notice>}
        {err && <Notice tone="error">{err}</Notice>}
        <button type="button" className="btn-danger mt-2" onClick={() => setConfirm(true)} data-testid="delete-all">
          <Icon name="trash" /> {t("more.delete")}
        </button>
      </Card>

      <Sheet open={confirm} title={t("more.deleteConfirm")} onClose={() => setConfirm(false)}>
        <p className="mb-4 text-body text-label2">{t("more.deleteBody")}</p>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button type="button" className="btn-secondary" onClick={() => setConfirm(false)}>
            {t("common.cancel")}
          </button>
          <button type="button" className="btn-danger" onClick={wipe}>
            {t("common.delete")}
          </button>
        </div>
      </Sheet>
    </div>
  );
}
