export type Level = "low" | "caution" | "high" | "critical";
export type Lang = "en" | "hi";

export interface Risk {
  score: number;
  level: Level;
  stage: string;
  summary: string;
  what_to_do: string[];
  tactics: string[];
}
export interface Line {
  turn: number;
  speaker: "scammer" | "persona" | "victim" | "caller";
  text: string;
  guarded?: boolean;
  move?: string | null;
}
export interface TimelinePoint {
  turn: number;
  score: number;
  stage: string;
  tactics: string[];
}
export interface EvidenceItem {
  type: string;
  value: string;
  confidence: number;
  turn?: number;
  mentions?: number;
}
export interface Source {
  title: string;
  url: string;
  snippet: string;
}
export interface Verification {
  kind: "advisory" | "claim_check" | "report_search";
  query: string;
  status: "ok" | "no_results" | "unavailable";
  sources: Source[];
  note: string;
  cached?: boolean;
}
export interface MemoryHit {
  script: string;
  banner: string;
  hit_turn: number;
  earlier_incident_id: number | null;
  earlier_detect_turn: number | null;
  seen_count: number;
}
export interface SessionSummary {
  risk_peak?: number;
  level?: Level;
  detect_turn?: number | null;
  time_wasted_s?: number;
  incident_id?: number | null;
  session_id?: string;
  ended_reason?: string;
  replay?: boolean;
}
export interface Scenario {
  id: string;
  title: string;
  language: string;
  agency: string;
}
export type Mode = "shield" | "honeypot" | "manual";
