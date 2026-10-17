import next from "eslint-config-next/core-web-vitals";

const config = [
  ...next,
  {
    rules: {
      // Intentional: browser-only state (localStorage, speech support, URL hash) is read after mount
      // to avoid SSR hydration mismatches, and data hooks fetch in effects.
      "react-hooks/set-state-in-effect": "off",
    },
  },
  { ignores: [".next/**", "node_modules/**", "e2e/**", "playwright.config.ts"] },
];

export default config;
