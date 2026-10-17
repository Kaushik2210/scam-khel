// Small inline icon set (SF Symbols equivalent). Decorative by default: pair with visible text.
const P: Record<string, string> = {
  shield: "M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6l7-3z",
  play: "M8 5l11 7-11 7V5z",
  stop: "M6 6h12v12H6z",
  alert: "M12 3l10 18H2L12 3zm0 7v5m0 3v.01",
  check: "M5 13l4 4L19 7",
  doc: "M7 3h7l5 5v13H7V3zm7 0v5h5M10 13h6M10 17h6",
  users: "M9 11a3 3 0 100-6 3 3 0 000 6zm-6 9c0-3 3-5 6-5s6 2 6 5m2-9a3 3 0 100-6m3 11c0-2-1-4-3-4.5",
  brain: "M9 4a3 3 0 00-3 3 3 3 0 00-2 5 3 3 0 002 5 3 3 0 006 0V4a3 3 0 00-3 0zm6 0a3 3 0 013 3 3 3 0 012 5 3 3 0 01-2 5 3 3 0 01-6 0",
  info: "M12 8v.01M11 12h1v5h1M12 3a9 9 0 100 18 9 9 0 000-18z",
  download: "M12 4v11m0 0l-4-4m4 4l4-4M5 20h14",
  phone: "M6 3h4l2 5-2.5 1.5a11 11 0 005 5L16 12l5 2v4a2 2 0 01-2 2A16 16 0 014 5a2 2 0 012-2z",
  home: "M4 11l8-7 8 7v9h-5v-6H9v6H4v-9z",
  more: "M5 12h.01M12 12h.01M19 12h.01",
  clock: "M12 7v5l3 2M12 3a9 9 0 100 18 9 9 0 000-18z",
  link: "M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1",
  trash: "M4 7h16M9 7V4h6v3m-8 0l1 13h8l1-13",
  globe: "M12 3a9 9 0 100 18 9 9 0 000-18zM3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18",
  mic: "M12 3a3 3 0 013 3v6a3 3 0 01-6 0V6a3 3 0 013-3zM6 11a6 6 0 0012 0M12 17v4",
};

export function Icon({ name, size = 20 }: { name: keyof typeof P | string; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      <path d={P[name] ?? P.info} />
    </svg>
  );
}
