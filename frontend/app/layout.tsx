import type { Metadata, Viewport } from "next";
import { Space_Grotesk, Plus_Jakarta_Sans, Noto_Sans_Devanagari } from "next/font/google";
import "./globals.css";
import { CursorRing } from "@/components/Cursor";
import { Providers } from "@/components/Providers";
import { THEME_INIT_SCRIPT } from "@/lib/theme";

const display = Space_Grotesk({ subsets: ["latin"], variable: "--font-display", display: "swap" });
const body = Plus_Jakarta_Sans({ subsets: ["latin"], variable: "--font-body", display: "swap" });
const deva = Noto_Sans_Devanagari({ subsets: ["devanagari"], display: "swap" });

export const metadata: Metadata = {
  title: "SCAM-KHEL: family shield against digital-arrest scams",
  description:
    "Detect fake-police scam calls, waste scammers' time with a simulated decoy, alert your family and draft a complaint. Hackathon demo: simulation only.",
};
export const viewport: Viewport = { width: "device-width", initialScale: 1, colorScheme: "light dark" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark" className={`${display.variable} ${body.variable} ${deva.className}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body>
        <div className="aurora" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
        <CursorRing />
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-50 focus:rounded-ctl focus:bg-tint focus:px-4 focus:py-3 focus:text-tint-on"
        >
          Skip to main content
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
