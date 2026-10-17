import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "@/components/Providers";

export const metadata: Metadata = {
  title: "SCAM-KHEL: family shield against digital-arrest scams",
  description:
    "Detect fake-police scam calls, waste scammers' time with a simulated decoy, alert your family and draft a complaint. Hackathon demo: simulation only.",
};
export const viewport: Viewport = { width: "device-width", initialScale: 1, colorScheme: "dark light" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
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
