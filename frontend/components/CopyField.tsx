"use client";

import { useRef, useState } from "react";
import { Icon } from "./Icon";
import { useI18n } from "@/lib/i18n";

/** One form field: label, the exact text to paste, and a Copy button with spoken confirmation. */
export function CopyField({ label, value, multiline = false }: { label: string; value: string; multiline?: boolean }) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(value);
    } catch {
      // clipboard blocked: select the text so Ctrl/Cmd+C works
      const el = box.current;
      if (el) {
        const range = document.createRange();
        range.selectNodeContents(el);
        const sel = window.getSelection();
        sel?.removeAllRanges();
        sel?.addRange(range);
      }
      return;
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };
  return (
    <div className="border-b border-sep py-3 last:border-0">
      <div className="mb-1.5 text-footnote font-semibold text-label2">{label}</div>
      <div className="flex items-start gap-2">
        <div
          ref={box}
          className={`min-h-[44px] flex-1 rounded-ctl bg-raised px-3 py-2.5 text-callout ${
            multiline ? "whitespace-pre-wrap break-words leading-6" : "break-words font-mono"
          }`}
          data-testid="copy-value"
        >
          {value}
        </div>
        <button type="button" className="btn-secondary !min-h-[44px] shrink-0" onClick={copy} aria-label={`${t("report.copy")}: ${label}`}>
          <Icon name={copied ? "check" : "doc"} size={18} />
          <span className="hidden sm:inline">{copied ? t("report.copied") : t("report.copy")}</span>
          <span className="sr-only" role="status" aria-live="polite">
            {copied ? t("report.copied") : ""}
          </span>
        </button>
      </div>
    </div>
  );
}
