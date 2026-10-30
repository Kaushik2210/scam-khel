import type { Config } from "tailwindcss";

// Tokens map to CSS variables (see app/globals.css) so light/dark and contrast adapt automatically.
const v = (name: string) => `var(--${name})`;
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: v("bg"),
        surface: v("surface"),
        raised: v("raised"),
        label: v("label"),
        label2: v("label-2"),
        label3: v("label-3"),
        sep: v("separator"),
        tint: v("tint"),
        accent: v("accent"),
        "tint-on": v("tint-on"),
        ok: v("ok"),
        warn: v("warn"),
        danger: v("danger"),
        crit: v("crit"),
        "ok-bg": v("ok-bg"),
        "warn-bg": v("warn-bg"),
        "danger-bg": v("danger-bg"),
        "crit-bg": v("crit-bg"),
      },
      fontFamily: {
        sans: ["var(--font-body)", "Noto Sans Devanagari", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-body)", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SF Mono", "Menlo", "Consolas", "monospace"],
      },
      // Apple text styles in rem (Dynamic Type equivalent: scales with the user's font-size setting)
      fontSize: {
        caption: ["0.75rem", { lineHeight: "1rem" }],
        footnote: ["0.8125rem", { lineHeight: "1.125rem" }],
        subhead: ["0.9375rem", { lineHeight: "1.25rem" }],
        callout: ["1rem", { lineHeight: "1.3125rem" }],
        body: ["1.0625rem", { lineHeight: "1.375rem" }],
        headline: ["1.0625rem", { lineHeight: "1.375rem", fontWeight: "600" }],
        title2: ["1.375rem", { lineHeight: "1.75rem", fontWeight: "600" }],
        title1: ["1.75rem", { lineHeight: "2.125rem", fontWeight: "700" }],
        large: ["2.125rem", { lineHeight: "2.5625rem", fontWeight: "700" }],
      },
      borderRadius: { card: "14px", ctl: "12px" },
      minHeight: { tap: "44px", tapxl: "64px" },
      minWidth: { tap: "44px" },
    },
  },
  plugins: [],
};
export default config;
