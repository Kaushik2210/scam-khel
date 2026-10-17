"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError, wsUrl } from "./api";
import type {
  EvidenceItem,
  Level,
  Line,
  MemoryHit,
  Mode,
  Risk,
  SessionSummary,
  TimelinePoint,
  Verification,
} from "./types";

export type Status = "idle" | "connecting" | "running" | "ended" | "error";

export interface AlertNote {
  level: string;
  sent: number;
  skipped: string | null;
}

export interface SessionState {
  status: Status;
  sessionId: string | null;
  transcript: Line[];
  risk: Risk | null;
  timeline: TimelinePoint[];
  evidence: EvidenceItem[];
  verifications: Verification[];
  timeWasted: number;
  engaged: number;
  memoryHit: MemoryHit | null;
  alerts: AlertNote[];
  summary: SessionSummary | null;
  replay: boolean;
  budgetNotice: string | null;
  error: string | null;
  simulation: boolean;
}

const initial: SessionState = {
  status: "idle",
  sessionId: null,
  transcript: [],
  risk: null,
  timeline: [],
  evidence: [],
  verifications: [],
  timeWasted: 0,
  engaged: 0,
  memoryHit: null,
  alerts: [],
  summary: null,
  replay: false,
  budgetNotice: null,
  error: null,
  simulation: true,
};

type Ev = Record<string, any> & { type: string };

export function reduce(s: SessionState, e: Ev): SessionState {
  switch (e.type) {
    case "transcript":
      return {
        ...s,
        status: s.status === "connecting" ? "running" : s.status,
        transcript: [...s.transcript, { turn: e.turn, speaker: e.speaker, text: e.text }],
      };
    case "persona_reply":
      return {
        ...s,
        timeWasted: e.time_wasted_s ?? s.timeWasted,
        engaged: s.engaged + 1,
        transcript: [
          ...s.transcript,
          { turn: e.turn, speaker: "persona", text: e.text, guarded: e.guarded, move: e.move },
        ],
      };
    case "risk": {
      const risk: Risk = {
        score: e.score,
        level: e.level as Level,
        stage: e.stage,
        summary: e.summary,
        what_to_do: e.what_to_do ?? [],
        tactics: e.active_tactics ?? e.tactics ?? [],
      };
      return {
        ...s,
        risk,
        timeline: [...s.timeline, { turn: e.turn, score: e.score, stage: e.stage, tactics: risk.tactics }],
      };
    }
    case "evidence": {
      const it = e.item as EvidenceItem;
      const rest = s.evidence.filter((x) => !(x.type === it.type && x.value === it.value));
      return { ...s, evidence: [...rest, it] };
    }
    case "verification":
      return { ...s, verifications: [...s.verifications, e as unknown as Verification] };
    case "memory_hit":
      return { ...s, memoryHit: e as unknown as MemoryHit };
    case "alert_sent":
      return { ...s, alerts: [...s.alerts, { level: e.level, sent: e.sent, skipped: e.skipped }] };
    case "budget_notice":
      return { ...s, budgetNotice: e.message, replay: s.replay || !!e.replay_source };
    case "summary":
      return { ...s, status: "ended", summary: e as unknown as SessionSummary };
    case "error":
      return { ...s, status: "error", error: e.message ?? "error" };
    default:
      return s;
  }
}

export function useSession() {
  const [state, setState] = useState<SessionState>(initial);
  const ws = useRef<WebSocket | null>(null);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      ws.current?.close();
    };
  }, []);

  const send = useCallback((msg: object) => {
    if (ws.current?.readyState === WebSocket.OPEN) ws.current.send(JSON.stringify(msg));
  }, []);

  const start = useCallback(
    async (opts: { mode: Mode; scenario: string; language: string; speed?: number }) => {
      ws.current?.close();
      setState({ ...initial, status: "connecting", simulation: opts.mode !== "shield" });
      try {
        const created = await api<{ id: string; ws: string; replay: boolean; notice: string | null }>(
          "/api/sessions",
          { method: "POST", body: JSON.stringify({ ...opts, consent: true }) },
        );
        if (!alive.current) return;
        setState((s) => ({ ...s, sessionId: created.id, replay: created.replay, budgetNotice: created.notice }));
        const sock = new WebSocket(wsUrl(created.ws));
        ws.current = sock;
        sock.onopen = () => {
          if (opts.mode !== "shield") send({ type: "control", action: "start", speed: opts.speed ?? 1 });
          else setState((s) => ({ ...s, status: "running" }));
        };
        sock.onmessage = (m) => {
          try {
            const ev = JSON.parse(m.data) as Ev;
            setState((s) => reduce(s, ev));
          } catch {
            /* ignore malformed frame */
          }
        };
        sock.onerror = () =>
          setState((s) => (s.status === "ended" ? s : { ...s, status: "error", error: "connection" }));
        sock.onclose = () =>
          setState((s) => (s.status === "running" || s.status === "connecting" ? { ...s, status: "ended" } : s));
      } catch (err) {
        setState((s) => ({
          ...s,
          status: "error",
          error: err instanceof ApiError ? err.message : "Unexpected error",
        }));
      }
    },
    [send],
  );

  const sendText = useCallback(
    (text: string, speaker: "caller" | "victim" = "victim") => send({ type: "utterance", text, speaker }),
    [send],
  );
  const takeover = useCallback(() => send({ type: "control", action: "takeover" }), [send]);
  const stop = useCallback(() => send({ type: "control", action: "stop" }), [send]);
  const reset = useCallback(() => {
    ws.current?.close();
    setState(initial);
  }, []);

  return { state, start, sendText, takeover, stop, reset };
}
