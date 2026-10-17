"use client";

import { ConsentProvider } from "./Consent";
import { Shell } from "./Shell";
import { I18nProvider } from "@/lib/i18n";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <I18nProvider>
      <ConsentProvider>
        <Shell>{children}</Shell>
      </ConsentProvider>
    </I18nProvider>
  );
}
