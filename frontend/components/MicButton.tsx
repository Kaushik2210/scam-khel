"use client";

import { useEffect, useRef, useState } from "react";
import { Icon } from "./Icon";
import { useI18n } from "@/lib/i18n";
import { canListen, listen } from "@/lib/voice";

/** Dictate into a text field. Hidden when the browser has no speech recognition. */
export function MicButton({ onText, big = false }: { onText: (t: string) => void; big?: boolean }) {
  const { t, lang } = useI18n();
  const [supported, setSupported] = useState(false);
  const [on, setOn] = useState(false);
  const stop = useRef<(() => void) | null>(null);
  useEffect(() => setSupported(canListen()), []);
  useEffect(() => () => stop.current?.(), []);
  if (!supported) return null;
  return (
    <button
      type="button"
      className={`btn-secondary ${big ? "!min-h-tapxl" : ""}`}
      aria-pressed={on}
      onClick={() => {
        if (on) {
          stop.current?.();
          return;
        }
        setOn(true);
        stop.current = listen(lang, onText, () => setOn(false));
      }}
    >
      <Icon name="mic" /> {on ? t("voice.listening") : t("voice.mic")}
    </button>
  );
}
