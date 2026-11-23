export type Reference = { number: number; source_id: string; title: string; heading: string; quote: string; document_id: string; document_hash: string; topic_id: string };
export type Message = { id: string; run_id: string; role: "user" | "assistant"; kind: "question" | "answer" | "clarification" | "reply"; content: string; status: string; references: Reference[]; created_at: string };
export type Run = { id: string; conversation_id: string; status: "running" | "awaiting_clarification" | "completed" | "failed" | "cancelled"; question: string; answer: string | null; error: string | null; interrupt_id: string | null; clarification_question: string | null; version: number; active_ms: number; wait_ms: number; created_at: string; updated_at: string; input_tokens: number | null; output_tokens: number | null; model?: string; reasoning_effort?: string };
export type Conversation = { id: string; title: string; created_at: string; updated_at: string };
export type Topic = { id: string; name: string; description: string; documents: { id: string; title: string; available: boolean; revision: string }[] };
export type Config = { model: string; reasoning_effort: string; configured: boolean; tracing_enabled: boolean; documents_count: number };
export type TurnResult = { run: Run; messages: Message[] };
export type RunDetail = { run: Run; events: { id: string; event: string; created_at: string; duration_ms: number | null; payload: Record<string, unknown>; execution_id: string; span_id: string; parent_span_id: string | null }[]; requests: { id: string; route: string; status: number; duration_ms: number; client_ms: number | null; created_at: string; execution_id?: string; proxy_id?: string }[]; messages: Message[]; totals: { events: number; messages: number; requests: number } };

export class ApiError extends Error {
  constructor(message: string, public status: number, public requestId: string | null) { super(message); }
}

export async function api<T>(path: string, init?: RequestInit): Promise<{ data: T; requestId: string | null }> {
  const response = await fetch(`/api${path}`, { cache: "no-store", ...init, headers: { "Content-Type": "application/json", ...init?.headers } });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(typeof body?.detail === "string" ? body.detail : `Request failed (${response.status}). Try again.`, response.status, response.headers.get("X-Request-ID"));
  return { data: body as T, requestId: response.headers.get("X-Request-ID") };
}

export function reportPaint(requestId: string | null, started: number, outcome: string) {
  if (!requestId) return;
  requestAnimationFrame(() => requestAnimationFrame(() => {
    void api(`/observability/requests/${encodeURIComponent(requestId)}/client`, {
      method: "POST", body: JSON.stringify({ duration_ms: performance.now() - started, outcome }),
    }).catch(() => { /* Advisory browser timing must never interrupt a conversation. */ });
  }));
}

export function duration(ms: number | null | undefined) {
  return ms == null ? "Not recorded" : ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`;
}

export function timestamp(value: string) {
  return new Date(value.endsWith("Z") || /[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`).toLocaleString();
}
