"use client";

import { createContext, useCallback, useContext, useRef, useState } from "react";
import { giveConsent, hasConsent } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { Sheet } from "./Sheet";

const Ctx = createContext<() => Promise<boolean>>(async () => true);

/** DPDP-style consent: purpose, what is stored, retention, how to delete. Record kept server-side too. */
export function ConsentProvider({ children }: { children: React.ReactNode }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const resolver = useRef<((v: boolean) => void) | null>(null);

  const require = useCallback(() => {
    if (hasConsent()) return Promise.resolve(true);
    setAgreed(false);
    setOpen(true);
    return new Promise<boolean>((res) => {
      resolver.current = res;
    });
  }, []);

  const finish = (ok: boolean) => {
    if (ok) giveConsent();
    setOpen(false);
    resolver.current?.(ok);
    resolver.current = null;
  };

  return (
    <Ctx.Provider value={require}>
      {children}
      <Sheet open={open} title={t("consent.title")} locked labelId="consent-title">
        <p className="mb-3 text-body text-label2">{t("consent.intro")}</p>
        <ul className="mb-4 list-disc space-y-2 pl-5 text-callout text-label2">
          <li>{t("consent.purpose")}</li>
          <li>{t("consent.stored")}</li>
          <li>{t("consent.retention")}</li>
          <li>{t("consent.delete")}</li>
          <li>{t("consent.llm")}</li>
        </ul>
        <label className="mb-4 flex min-h-tap cursor-pointer items-center gap-3 text-body">
          <input
            type="checkbox"
            className="h-6 w-6 accent-[var(--tint)]"
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
          />
          {t("consent.agree")}
        </label>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button type="button" className="btn-plain" onClick={() => finish(false)}>
            {t("consent.decline")}
          </button>
          <button type="button" className="btn-primary" disabled={!agreed} onClick={() => finish(true)}>
            {t("consent.accept")}
          </button>
        </div>
      </Sheet>
    </Ctx.Provider>
  );
}

export const useRequireConsent = () => useContext(Ctx);
