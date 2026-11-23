"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@astryxdesign/core/Button";
import { HStack, VStack } from "@astryxdesign/core/Layout";
import { TextInput } from "@astryxdesign/core/TextInput";
import { api, duration, timestamp, type Config } from "@/lib/api";
import { label, number, queryTokens, type Ledger, type Logs, type Summary, type Window } from "@/lib/observability";
import { ObservabilityMetrics } from "./observability-metrics";
import { TraceDetail } from "./trace-detail";

type View = "metrics" | "traces" | "logs";

export function RunInspector({ initialRunId = null }: { initialRunId?: string | null }) {
  const [view, setView] = useState<View>(initialRunId ? "traces" : "metrics");
  const [window, setWindow] = useState<Window>(initialRunId ? "all" : "24h");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [config, setConfig] = useState<Config | null>(null);
  const [ledger, setLedger] = useState<Ledger | null>(null);
  const [logs, setLogs] = useState<Logs | null>(null);
  const [selected, setSelected] = useState<string | null>(initialRunId);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [level, setLevel] = useState("all");
  const [source, setSource] = useState("sqlite");
  const [page, setPage] = useState(0);
  const [revision, setRevision] = useState(0);
  const [auto, setAuto] = useState(false);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updated, setUpdated] = useState<string | null>(null);
  useEffect(() => {
    const timer = setTimeout(() => { setQuery(search.trim()); setPage(0); }, 300);
    return () => clearTimeout(timer);
  }, [search]);
  useEffect(() => {
    if (!auto) return;
    const timer = setInterval(() => {
      if (!document.hidden) setRevision(value => value + 1);
    }, 15000);
    return () => clearInterval(timer);
  }, [auto]);
  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      setBusy(true); setError(null);
      try {
        const params = new URLSearchParams({ window, search: query, limit: "50", offset: String(page * 50) });
        const init = { signal: controller.signal };
        const [totals, settings, records] = await Promise.all([
          api<Summary>(`/observability/summary?window=${window}`, init),
          api<Config>("/config", init),
          view === "logs"
            ? api<Logs>(`/observability/logs?${params}&source=${source}&level=${level}`, init)
            : api<Ledger>(`/observability/runs?${params}&status=${view === "metrics" ? "" : status}`, init),
        ]);
        if (controller.signal.aborted) return;
        setSummary(totals.data); setConfig(settings.data);
        if (view === "logs") setLogs(records.data as Logs);
        else {
          const next = records.data as Ledger;
          setLedger(next);
          setSelected(current => current ?? next.items[0]?.id ?? null);
        }
        setUpdated(new Date().toISOString());
      } catch (cause) {
        if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : "Could not load observability data.");
      } finally { if (!controller.signal.aborted) setBusy(false); }
    }
    void load();
    return () => controller.abort();
  }, [view, window, query, status, level, source, page, revision]);

  function switchView(next: View) { setView(next); setPage(0); setSearch(""); setQuery(""); setError(null); }
  function openRun(id: string) {
    setSelected(id);
    if (view !== "traces") switchView("traces");
    globalThis.window.history.replaceState(null, "", `/observability?run=${encodeURIComponent(id)}`);
  }
  const records = view === "logs" ? logs : ledger;
  return <main className="observability">
    <HStack as="header" className="obs-header" hAlign="between" vAlign="center" wrap="wrap" gap={4}>
      <VStack gap={2}>
        <Link href="/" className="obs-back">← Floor Guide</Link>
        <h1>Observability</h1>
        <p className="muted">Follow a question from request to answer.</p>
      </VStack>
      <HStack gap={3} vAlign="end" wrap="wrap">
        <label className="obs-field">Time window<select value={window} onChange={event => { setWindow(event.target.value as Window); setPage(0); }}>
          <option value="1h">Last hour</option><option value="24h">Last 24 hours</option><option value="7d">Last 7 days</option><option value="all">All time</option>
        </select></label>
        <Button label="Refresh" onClick={() => setRevision(value => value + 1)} isLoading={busy} />
      </HStack>
    </HStack>
    <HStack className="obs-toolbar" hAlign="between" vAlign="center" wrap="wrap" gap={3}>
      <HStack as="nav" gap={1} aria-label="Observability views">
        {(["metrics", "traces", "logs"] as const).map(tab => <Button key={tab} label={tab[0].toUpperCase() + tab.slice(1)} variant={view === tab ? "primary" : "ghost"} aria-current={view === tab ? "page" : undefined} onClick={() => switchView(tab)} />)}
      </HStack>
      <HStack gap={4} vAlign="center" wrap="wrap">
        <small aria-live="polite">{busy ? "Updating…" : error ? "Refresh failed · showing previous data" : updated ? `Updated ${new Date(updated).toLocaleTimeString()}` : "Connecting…"}</small>
        <label className="obs-auto"><input type="checkbox" checked={auto} onChange={event => setAuto(event.target.checked)} /> Auto-refresh · 15s</label>
      </HStack>
    </HStack>
    {error && <p role="alert" className="inline-error">{error} Check that the backend is running, then refresh.</p>}
    <section aria-label={`${view} view`} aria-busy={busy} className="obs-content">
      {view === "metrics" && (summary ? <ObservabilityMetrics summary={summary} runs={ledger?.items ?? []} onRun={openRun} onTraces={() => switchView("traces")} /> : <p role="status" className="obs-empty">{error ? "Metrics are unavailable until the connection is restored." : "Loading saved measurements…"}</p>)}
      {view !== "metrics" && <>
        <HStack className="obs-filters" gap={4} vAlign="end" wrap="wrap">
          <TextInput label={view === "traces" ? "Search traces" : "Search logs"} type="search" value={search} onChange={value => setSearch(value.slice(0, 200))} placeholder={view === "traces" ? "Question, session or turn ID…" : "Event, request ID or payload…"} hasClear containerClassName="obs-search" />
          {view === "traces" ? <label className="obs-field">Outcome<select value={status} onChange={event => { setStatus(event.target.value); setPage(0); }}><option value="">All outcomes</option>{["completed", "failed", "running", "awaiting_clarification", "cancelled"].map(s => <option value={s} key={s}>{label(s)}</option>)}</select></label> : <>
            <label className="obs-field">Source<select value={source} onChange={event => { setSource(event.target.value); setPage(0); }}><option value="sqlite">SQLite actions + HTTP</option><option value="application">Application JSON logs</option></select></label>
            <label className="obs-field">Severity<select value={level} onChange={event => { setLevel(event.target.value); setPage(0); }}><option value="all">All severities</option>{["info", "warning", "error"].map(s => <option key={s} value={s}>{s}</option>)}</select></label>
          </>}
          <small>{number(records?.total)} matching {view === "traces" ? "turns" : "records"}</small>
        </HStack>
        {view === "traces" ? <section className="obs-trace-grid">
          <aside className="obs-run-list" aria-label="Recorded traces">
            {!ledger?.items.length && <p className="obs-empty">{busy ? "Loading traces…" : "No traces match. Widen the time window or change the filters. Ask a question in Floor Guide to record a new trace."}</p>}
            {ledger?.items.map(run => <button type="button" className={`obs-run ${selected === run.id ? "obs-selected" : ""}`} key={run.id} onClick={() => openRun(run.id)} aria-current={selected === run.id ? "true" : undefined}>
              <HStack hAlign="between" gap={2}><small className={`obs-status obs-${run.status}`}>{label(run.status)}</small><small>{duration(run.active_ms)}</small></HStack>
              <strong>{run.question}</strong><small>{number(queryTokens(run))} tokens · {timestamp(run.created_at)}</small><code>{run.id.slice(0, 8)} · session {run.conversation_id.slice(0, 8)}</code>
            </button>)}
          </aside>
          <TraceDetail key={selected} id={selected} revision={revision} tracing={config?.tracing_enabled ?? false} />
        </section> : <>
          <p className="obs-note">{source === "sqlite" ? "Persisted action events and HTTP records. Severity is classified from stored outcomes and HTTP status; these are not Python logger levels. Inspector requests are excluded." : "Rotating application.jsonl files, newest first. Showing matches from the latest 5,000 file records. These diagnostics are stored on disk separately from SQLite."}</p>
          <section className="obs-log-list" aria-label="Log records">
            {!logs?.items.length && <p className="obs-empty">{busy ? "Loading logs…" : "No log records match. Change the source, severity, search or time window."}</p>}
            {logs?.items.map(log => <details className="obs-log" key={log.id}>
              <summary><time>{timestamp(log.created_at)}</time><b className={`obs-status obs-${log.level}`}>{log.level}</b><strong>{log.event}</strong><small>{log.source} · {duration(log.duration_ms)}</small></summary>
              <HStack hAlign="between" wrap="wrap" gap={3}><code>{log.run_id ? `Turn ${log.run_id}` : `Record ${log.id}`}</code>{log.run_id && <Button label="Inspect trace" size="sm" onClick={() => { setWindow("all"); openRun(log.run_id!); }} />}</HStack>
              <pre>{JSON.stringify({ ...log.payload, conversation_id: log.conversation_id, execution_id: log.execution_id }, null, 2)}</pre>
            </details>)}
          </section>
        </>}
        <HStack className="obs-pagination" hAlign="between" vAlign="center" wrap="wrap" gap={3}>
          <small>{records?.total ? `${page * 50 + 1}–${Math.min(page * 50 + 50, records.total)} of ${number(records.total)}` : "0 records"}</small>
          <HStack gap={2}><Button label="Previous" size="sm" isDisabled={page === 0 || busy} onClick={() => setPage(value => value - 1)} /><Button label="Next" size="sm" isDisabled={busy || !records || (page + 1) * 50 >= records.total} onClick={() => setPage(value => value + 1)} /></HStack>
        </HStack>
      </>}
    </section>
    <HStack as="footer" className="obs-footer" hAlign="between" wrap="wrap" gap={3}><small>Local inspector · Saved data only · Timestamps in your timezone</small><small>{config?.tracing_enabled ? "External tracing configured · Export delivery is not recorded" : "External tracing disabled · Local inspection available"}</small></HStack>
  </main>;
}
