"use client";

import { useEffect, useRef, useState } from "react";
import { Icon } from "./Icon";
import { Notice } from "./Panels";
import { Sheet } from "./Sheet";
import { useI18n } from "@/lib/i18n";
import { canListen, listenContinuous } from "@/lib/voice";

const OK_KEY = "sk_listen_ok";

/** Live "Listen mode": browser speech-to-text of a call on speaker, fed line by line into Shield. */
export function ListenPanel({ onLine, onStarted }: { onLine: (line: string) => void; onStarted: () => Promise<boolean> }) {
  const { t, lang } = useI18n();
  const [supported, setSupported] = useState(true);
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [heard, setHeard] = useState<string[]>([]);
  const [denied, setDenied] = useState(false);
  const [askConsent, setAskConsent] = useState(false);
  const stop = useRef<(() => void) | null>(null);
  useEffect(() => setSupported(canListen()), []);
  useEffect(() => () => stop.current?.(), []);

  const begin = async () => {
    setDenied(false);
    if (!(await onStarted())) return; // analysis consent / session could not start
    setListening(true);
    stop.current = listenContinuous(
      lang,
      (text) => {
        setHeard((h) => [...h.slice(-5), text]);
        onLine(text);
      },
      setInterim,
      (reason) => {
        setListening(false);
        if (reason === "denied") setDenied(true);
      },
    );
  };
  const onStart = () => {
    let ok = false;
    try {
      ok = window.localStorage.getItem(OK_KEY) === "1";
    } catch {
      /* ask every time */
    }
    if (ok) begin();
    else setAskConsent(true);
  };
  const consent = () => {
    try {
      window.localStorage.setItem(OK_KEY, "1");
    } catch {
      /* ignore */
    }
    setAskConsent(false);
    begin();
  };

  if (!supported) return <Notice tone="warn">{t("listen.unsupported")}</Notice>;
  return (
    <section className="card space-y-4" aria-label={t("listen.title")}>
      <p className="text-callout text-label2">{t("listen.how")}</p>
      <ul className="list-disc space-y-1 pl-5 text-footnote text-label2">
        <li>{t("listen.tip1")}</li>
        <li>{t("listen.tip2")}</li>
        <li>{t("listen.tip3")}</li>
      </ul>
      <div className="flex flex-col items-center gap-3 py-2">
        <button
          type="button"
          onClick={listening ? () => stop.current?.() : onStart}
          aria-pressed={listening}
          data-testid="listen-toggle"
          className={`flex h-24 w-24 items-center justify-center rounded-full text-white shadow-lg transition-transform active:scale-95 ${
            listening ? "bg-crit motion-safe:animate-pulse" : "bg-tint"
          }`}
          aria-label={listening ? t("listen.stop") : t("listen.start")}
        >
          <Icon name={listening ? "stop" : "mic"} size={38} />
        </button>
        <p className="text-headline" role="status">
          {listening ? t("listen.listening") : t("listen.start")}
        </p>
      </div>
      {denied && <Notice tone="error">{t("listen.denied")}</Notice>}
      {(heard.length > 0 || interim) && (
        <div className="rounded-ctl bg-raised p-3" aria-live="off">
          <h3 className="mb-1 text-subhead font-semibold text-label2">{t("listen.heard")}</h3>
          <ul className="space-y-1 text-callout">
            {heard.map((h, i) => (
              <li key={i}>{h}</li>
            ))}
            {interim && <li className="text-label3">{interim}…</li>}
          </ul>
        </div>
      )}
      <Sheet open={askConsent} title={t("listen.consent.title")} onClose={() => setAskConsent(false)} labelId="listen-consent">
        <p className="mb-4 text-body text-label2">{t("listen.consent.body")}</p>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button type="button" className="btn-secondary" onClick={() => setAskConsent(false)}>
            {t("common.cancel")}
          </button>
          <button type="button" className="btn-primary" onClick={consent} data-testid="listen-allow">
            {t("listen.consent.ok")}
          </button>
        </div>
      </Sheet>
    </section>
  );
}
