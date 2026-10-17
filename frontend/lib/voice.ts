// Browser voice fallback (Web Speech API). NOT an NVIDIA model: documented honestly in README/About.
// Text mode never depends on this; every function degrades to a no-op.

interface Rec {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}
type RecCtor = new () => Rec;

function ctor(): RecCtor | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as { SpeechRecognition?: RecCtor; webkitSpeechRecognition?: RecCtor };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export const canListen = () => ctor() !== null;
export const canSpeak = () => typeof window !== "undefined" && "speechSynthesis" in window;

export function listen(lang: "en" | "hi", onText: (t: string) => void, onEnd: () => void): () => void {
  const C = ctor();
  if (!C) {
    onEnd();
    return () => {};
  }
  const r = new C();
  r.lang = lang === "hi" ? "hi-IN" : "en-IN";
  r.interimResults = false;
  r.continuous = false;
  r.onresult = (e) => {
    const out = Array.from(e.results as ArrayLike<ArrayLike<{ transcript: string }>>)
      .map((x) => x[0]?.transcript ?? "")
      .join(" ")
      .trim();
    if (out) onText(out);
  };
  r.onerror = onEnd;
  r.onend = onEnd;
  r.start();
  return () => r.stop();
}

export function speak(text: string, lang: "en" | "hi") {
  if (!canSpeak()) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = lang === "hi" ? "hi-IN" : "en-IN";
  u.rate = 0.9;
  window.speechSynthesis.speak(u);
}

export const stopSpeaking = () => canSpeak() && window.speechSynthesis.cancel();

// ---- continuous listening (Listen mode) ----
interface LiveRec {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult:
    | ((e: { resultIndex: number; results: ArrayLike<{ isFinal: boolean; 0: { transcript: string } }> }) => void)
    | null;
  onerror: ((e: { error?: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}

/**
 * Listen continuously. Calls onFinal for each finished phrase and onInterim for the phrase in
 * progress. Browsers end recognition after silence, so it restarts until the returned stop() is called.
 * Audio never leaves the browser's speech engine path and is never stored by SCAM-KHEL.
 */
export function listenContinuous(
  lang: "en" | "hi",
  onFinal: (t: string) => void,
  onInterim: (t: string) => void,
  onEnd: (reason: "stopped" | "denied" | "error") => void,
): () => void {
  const C = ctor() as unknown as (new () => LiveRec) | null;
  if (!C) {
    onEnd("error");
    return () => {};
  }
  let stopped = false;
  const r = new C();
  r.lang = lang === "hi" ? "hi-IN" : "en-IN";
  r.interimResults = true;
  r.continuous = true;
  r.onresult = (e) => {
    let interim = "";
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const res = e.results[i];
      const text = res[0]?.transcript?.trim() ?? "";
      if (!text) continue;
      if (res.isFinal) onFinal(text);
      else interim += `${text} `;
    }
    onInterim(interim.trim());
  };
  r.onerror = (e) => {
    if (e.error === "not-allowed" || e.error === "service-not-allowed") {
      stopped = true;
      onEnd("denied");
    }
  };
  r.onend = () => {
    if (stopped) return;
    try {
      r.start(); // silence timeout: keep listening
    } catch {
      stopped = true;
      onEnd("error");
    }
  };
  try {
    r.start();
  } catch {
    onEnd("error");
  }
  return () => {
    stopped = true;
    onInterim("");
    try {
      r.stop();
    } catch {
      /* already stopped */
    }
    onEnd("stopped");
  };
}
