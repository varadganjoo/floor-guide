import type { Run, RunDetail } from "./api";

export type Window = "1h" | "24h" | "7d" | "all";
export type Latency = { count: number; p50_ms: number | null; p95_ms: number | null };
export type Summary = {
  window: Window; since: string; until: string; run_limit: number; request_limit: number;
  count: number; sessions: number; statuses: Record<Run["status"], number>;
  latency: { agent: Latency; server: Latency; client: Latency };
  requests: number; http_errors: number; events: number; provider_calls: number;
  usage: Record<string, { total: number | null; known: number }>;
  searches: number; no_results: number; clarified_turns: number; corrections_and_retries: number;
  stages: (Latency & { name: string })[];
  buckets: { at: string; count: number; completed: number; failed: number }[];
};
export type Ledger = { items: Run[]; total: number };
export type LogRecord = {
  id: string; created_at: string; event: string; level: string; source: string;
  run_id: string | null; conversation_id: string | null; execution_id: string | null;
  duration_ms: number | null; payload: Record<string, unknown>;
};
export type Logs = { items: LogRecord[]; total: number; source: string; scan_limit: number | null };
export const label = (value: string) => value.replaceAll("_", " ");
export const number = (value: number | null | undefined) => value == null ? "Unknown" : value.toLocaleString();
export const rate = (value: number, total: number) => total ? `${(100 * value / total).toFixed(1)}%` : "—";
export const queryTokens = (run: Pick<Run, "input_tokens" | "output_tokens">) =>
  run.input_tokens == null || run.output_tokens == null ? null : run.input_tokens + run.output_tokens;

export function epoch(value: string) {
  return Date.parse(value.endsWith("Z") || /[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`);
}

/** Spans are stored at completion; point events have no inferred duration. */
export function executionTimeline(events: RunDetail["events"]) {
  const spans = new Map(events.map(event => [event.span_id, event]));
  return Array.from(new Set(events.map(event => event.execution_id))).map(id => {
    const segment = events.filter(event => event.execution_id === id);
    const times = segment.map(event => {
      const end = epoch(event.created_at);
      return { event, start: end - Math.max(0, event.duration_ms ?? 0), end };
    });
    const start = Math.min(...times.map(time => time.start));
    const end = Math.max(...times.map(time => time.end));
    const width = Math.max(1, end - start);
    return { id, duration: end - start, rows: times.sort((a, b) => a.start - b.start).map(time => {
      let parent = time.event.parent_span_id;
      const seen = new Set([time.event.span_id]);
      let depth = 0;
      while (parent && spans.has(parent) && !seen.has(parent)) {
        seen.add(parent); depth++;
        parent = spans.get(parent)!.parent_span_id;
      }
      return { ...time, depth: Math.min(depth, 6),
        offset: Math.max(0, Math.min(100, (time.start - start) / width * 100)),
        width: Math.max(0, Math.min(100, (time.end - time.start) / width * 100)) };
    }) };
  });
}
