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
