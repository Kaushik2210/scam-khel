export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const CID_KEY = "sk_client_id";
const CONSENT_KEY = "sk_consent_v1";

function safeGet(k: string): string | null {
  try {
    return window.localStorage.getItem(k);
  } catch {
    return null;
  }
}
function safeSet(k: string, v: string) {
  try {
    window.localStorage.setItem(k, v);
  } catch {
    /* storage unavailable: the session still works, just not across reloads */
  }
}

let memoryId: string | null = null;
export function clientId(): string {
  if (typeof window === "undefined") return "ssr-placeholder";
  let id = memoryId ?? safeGet(CID_KEY);
  if (!id) {
    id = crypto.randomUUID();
    safeSet(CID_KEY, id);
  }
  memoryId = id;
  return id;
}
export function hasConsent(): boolean {
  return typeof window !== "undefined" && safeGet(CONSENT_KEY) === "granted";
}
export function giveConsent() {
  safeSet(CONSENT_KEY, "granted");
}
export function revokeConsent() {
  try {
    window.localStorage.removeItem(CONSENT_KEY);
  } catch {
    /* ignore */
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        "X-Client-Id": clientId(),
        ...(init.headers ?? {}),
      },
    });
  } catch {
    throw new ApiError(0, "Cannot reach the server. Check your connection and try again.");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const j = await res.json();
      detail = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, res.status === 429 ? "Too many requests. Please wait a moment." : detail);
  }
  return (await res.json()) as T;
}

export function wsUrl(path: string): string {
  return `${API.replace(/^http/, "ws")}${path}${path.includes("?") ? "&" : "?"}client_id=${clientId()}`;
}

/** Download an authenticated file (the client id header can't ride on a plain <a href>). */
export async function download(path: string, filename: string) {
  const res = await fetch(`${API}${path}`, { headers: { "X-Client-Id": clientId() } });
  if (!res.ok) throw new ApiError(res.status, "Download failed");
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
