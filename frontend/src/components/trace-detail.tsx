"use client";

import { useEffect, useState } from "react";
import { Button } from "@astryxdesign/core/Button";
import { HStack, VStack } from "@astryxdesign/core/Layout";
import { api, duration, timestamp, type Reference, type RunDetail } from "@/lib/api";
import { executionTimeline, label, number, queryTokens } from "@/lib/observability";
import { MessageContent } from "./message-content";
import { SourcePreview } from "./source-preview";

type Panel = "events" | "messages" | "requests";
export function TraceDetail({ id, revision, tracing }: { id: string | null; revision: number; tracing: boolean }) {
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [panel, setPanel] = useState<Panel>("events");
  const [source, setSource] = useState<Reference | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!id) return;
    const controller = new AbortController();
    void api<RunDetail>(`/observability/runs/${encodeURIComponent(id)}`, { signal: controller.signal }).then(({ data }) => {
      if (!controller.signal.aborted) { setDetail(data); setError(null); }
    }).catch(cause => { if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "Could not load this trace."); });
    return () => controller.abort();
  }, [id, revision, retry]);

  async function more() {
    if (!detail || !id) return;
    setBusy(true); setError(null);
    try {
      const { data } = await api<RunDetail>(`/observability/runs/${encodeURIComponent(id)}?${panel === "events" ? "event" : panel === "messages" ? "message" : "request"}_offset=${detail[panel].length}`);
      setDetail(current => current ? { ...current, [panel]: [...current[panel], ...data[panel]], totals: data.totals } : current);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Could not load more records."); }
    finally { setBusy(false); }
  }
  const run = detail?.run;
  return <section className="obs-trace-detail" aria-label="Selected trace details">
    {error && <HStack gap={3} wrap="wrap"><p role="alert" className="inline-error">{error}</p><Button label="Retry trace" size="sm" onClick={() => setRetry(value => value + 1)} /></HStack>}
    {!detail || !run ? <p role="status" className="obs-empty">{error ? "Trace details could not be loaded." : id ? "Loading the saved trace…" : "Select a trace to inspect its actions, transcript and requests."}</p> : <VStack gap={5}>
      <header><p className={`obs-status obs-${run.status}`}>{label(run.status)}</p><h2>{run.question}</h2><p className="obs-note">{run.model ?? "Model not recorded"} · Reasoning effort {run.reasoning_effort ?? "not recorded"}</p></header>
      <section className="obs-query-tokens" aria-label="Token usage for this query"><HStack gap={6} wrap="wrap"><VStack gap={1}><small>Total tokens</small><strong>{number(queryTokens(run))}</strong></VStack><VStack gap={1}><small>Input tokens</small><strong>{number(run.input_tokens)}</strong></VStack><VStack gap={1}><small>Output tokens</small><strong>{number(run.output_tokens)}</strong></VStack></HStack><p className="obs-note">Across recorded model and history-selection calls for this query, including retries and clarification resumes. Missing usage stays unknown. Expand a model call in the timeline for its individual usage.</p></section>
      <dl className="obs-identifiers"><dt>Turn</dt><dd>{run.id}</dd><dt>Session</dt><dd>{run.conversation_id}</dd><dt>Started</dt><dd>{timestamp(run.created_at)}</dd><dt>Agent active / human wait</dt><dd>{duration(run.active_ms)} / {duration(run.wait_ms)}</dd><dt>Input / output tokens</dt><dd>{run.input_tokens ?? "Unknown"} / {run.output_tokens ?? "Unknown"}</dd><dt>External trace</dt><dd>{tracing ? "Configured · Delivery status and link not recorded" : "Disabled · Local trace available"}</dd></dl>
      {run.error && <p className="inline-error" role="alert">{run.error}</p>}
      <HStack as="nav" gap={1} wrap="wrap" aria-label="Trace detail views">{(["events", "messages", "requests"] as const).map(tab => <Button size="sm" key={tab} label={`${tab === "events" ? "Timeline" : tab === "messages" ? "Transcript" : "HTTP requests"} (${detail.totals[tab]})`} variant={panel === tab ? "primary" : "ghost"} aria-current={panel === tab ? "page" : undefined} onClick={() => setPanel(tab)} />)}</HStack>
      {panel === "events" && <section className="obs-waterfall">
        <p className="obs-note">Each execution has its own time axis. Bars use completion time minus stored duration; points have no duration. Spans overlap. Human waits between executions are excluded.</p>
        {executionTimeline(detail.events).map(segment => <section key={segment.id} className="obs-execution"><HStack hAlign="between" gap={2} wrap="wrap"><h3>Execution {segment.id.slice(0, 8)}</h3><small>{duration(segment.duration)} observed range</small></HStack>
          {segment.rows.map(row => <details className="obs-span" key={row.event.id}>
            <summary><strong style={{ paddingInlineStart: `${row.depth}em` }}>{label(row.event.event)}</strong><svg viewBox="0 0 100 8" preserveAspectRatio="none" aria-hidden="true"><line x1="0" x2="100" y1="4" y2="4" className="obs-span-track" />{row.event.duration_ms == null ? <circle cx={Math.min(99, row.offset)} cy="4" r="1" className="obs-span-point" /> : <rect x={row.offset} width={Math.max(.4, row.width)} height="4" y="2" rx="1" className={row.event.event.includes("failed") || row.event.payload.outcome === "failed" ? "obs-span-error" : "obs-span-bar"} />}</svg><small>{duration(row.event.duration_ms)}</small></summary>
            <dl className="obs-identifiers"><dt>Recorded at</dt><dd>{timestamp(row.event.created_at)}</dd><dt>Execution</dt><dd>{row.event.execution_id}</dd><dt>Span</dt><dd>{row.event.span_id}</dd><dt>Parent</dt><dd>{row.event.parent_span_id ?? "Root"}</dd></dl><pre>{JSON.stringify(row.event.payload, null, 2)}</pre>
          </details>)}
        </section>)}
        {!detail.events.length && <p className="obs-empty">No action events were saved for this turn.</p>}
      </section>}
      {panel === "messages" && <section><p className="obs-note">Exact saved questions, clarification exchanges and delivered answers. Open a reference to inspect its evidence.</p>{detail.messages.map(message => <article key={message.id} className={`obs-message obs-message-${message.role}`}><HStack hAlign="between" gap={3} wrap="wrap"><strong>{message.role === "user" ? "Supervisor" : "Floor Guide"} · {message.kind}</strong><small>{timestamp(message.created_at)}</small></HStack><MessageContent message={message} onSource={setSource} /></article>)}{!detail.messages.length && <p className="obs-empty">No messages were saved for this turn.</p>}</section>}
      {panel === "requests" && <section><p className="obs-note">Server and advisory browser durations overlap; they are not summed. Proxy IDs link to the Next.js server logs; proxy duration is not persisted here.</p><section className="table-scroll"><table><thead><tr><th>Route / correlation</th><th>Status</th><th>Server</th><th>Browser</th></tr></thead><tbody>{detail.requests.map(request => <tr key={request.id}><td><code>{request.route}</code><small>Request {request.id}</small><small>Proxy {request.proxy_id ?? "Not recorded"}</small><small>Execution {request.execution_id ?? "Not recorded"}</small></td><td>{request.status}</td><td>{duration(request.duration_ms)}</td><td>{duration(request.client_ms)}</td></tr>)}</tbody></table></section>{!detail.requests.length && <p className="obs-empty">No linked requests were saved for this turn.</p>}</section>}
      {detail[panel].length < detail.totals[panel] && <Button label={`Load more (${detail[panel].length} of ${detail.totals[panel]})`} isLoading={busy} onClick={() => { void more(); }} />}
    </VStack>}
    <SourcePreview source={source} onClose={() => setSource(null)} />
  </section>;
}
