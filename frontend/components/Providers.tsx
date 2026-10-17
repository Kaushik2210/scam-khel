"use client";

import { ConsentProvider } from "./Consent";
import { Shell } from "./Shell";
import { I18nProvider } from "@/lib/i18n";
import { ThemeProvider } from "@/lib/theme";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <I18nProvider>
        <ConsentProvider>
          <Shell>{children}</Shell>
        </ConsentProvider>
      </I18nProvider>
    </ThemeProvider>
  );
}
