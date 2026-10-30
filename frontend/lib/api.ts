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

const ALLOW_CLIENT_PARAM = process.env.NEXT_PUBLIC_ALLOW_CLIENT_PARAM === "1";

let memoryId: string | null = null;
export function clientId(): string {
  if (typeof window === "undefined") return "ssr-placeholder";
  // ?client=<id> opens the app as the seeded demo user. It is OFF unless the build sets
  // NEXT_PUBLIC_ALLOW_CLIENT_PARAM=1: the client id is the only credential, so a link that
  // chose it for a visitor would let whoever sent the link read that visitor's data.
  const fromUrl = ALLOW_CLIENT_PARAM ? new URLSearchParams(window.location.search).get("client") : null;
  if (fromUrl && /^[A-Za-z0-9-]{8,64}$/.test(fromUrl)) {
    safeSet(CID_KEY, fromUrl);
    memoryId = fromUrl;
  }
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

/**
 * Websocket URL for a session. It carries the per-session ticket the API returned when the
 * session was created, never the long-lived client id, so the credential stays out of URLs
 * and the access logs that record them.
 */
export function wsUrl(path: string, ticket: string): string {
  return `${API.replace(/^http/, "ws")}${path}${path.includes("?") ? "&" : "?"}ticket=${encodeURIComponent(ticket)}`;
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
