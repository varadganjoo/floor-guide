import { Button } from "@astryxdesign/core/Button";
import { HStack, VStack } from "@astryxdesign/core/Layout";
import { duration, timestamp, type Run } from "@/lib/api";
import { label, number, queryTokens, rate, type Summary } from "@/lib/observability";

export function ObservabilityMetrics({ summary: s, runs, onRun, onTraces }: { summary: Summary; runs: Run[]; onRun: (id: string) => void; onTraces: () => void }) {
  const terminal = s.statuses.completed + s.statuses.failed;
  const stats = [
    ["Recorded turns", number(s.count), `${number(s.sessions)} sessions`],
    ["Completed", number(s.statuses.completed), `${rate(s.statuses.completed, terminal)} of completed + failed`],
    ["Failed", number(s.statuses.failed), `${number(s.statuses.cancelled)} cancelled separately`],
    ["Awaiting clarification", number(s.statuses.awaiting_clarification), `${number(s.statuses.running)} running`],
  ];
  const max = Math.max(1, ...s.buckets.map(bucket => bucket.count));
  const hours = Math.max(1 / 60, (Date.parse(s.until) - Date.parse(s.since)) / 3_600_000);
  return <VStack gap={6}>
    <p className="obs-note">{timestamp(s.since)} – {timestamp(s.until)} · Latest {number(s.run_limit)} turns within the selected window. Metrics are independent of trace and log search filters.</p>
    <section className="obs-stats" aria-label="Turn outcomes">{stats.map(([name, value, note]) => <article key={name}><p>{name}</p><strong>{value}</strong><small>{note}</small></article>)}</section>
    <section className="obs-chart-section">
      <HStack hAlign="between" vAlign="start" wrap="wrap" gap={4}><VStack gap={2}><h2>Question activity</h2><p className="muted">Turns accepted in each interval, grouped by current outcome.</p></VStack><VStack gap={1}><strong>{(s.count / hours).toFixed(1)} turns / hour</strong><small>Within this sampled window</small></VStack></HStack>
      {s.count === 0 ? <p className="obs-empty">No turns in this window. Ask a question in Floor Guide or select a wider time window.</p> : <figure className="obs-chart">
        <svg viewBox="0 0 960 190" role="img" aria-label={`Question activity: ${s.count} turns across 12 intervals. ${s.statuses.completed} completed and ${s.statuses.failed} failed.`}>
          {[0, .5, 1].map(fraction => <g key={fraction}><line x1="30" x2="950" y1={160 - fraction * 140} y2={160 - fraction * 140} className="obs-grid-line" /><text x="0" y={164 - fraction * 140}>{Math.round(max * fraction)}</text></g>)}
          {s.buckets.map((bucket, i) => {
            const completed = bucket.completed / max * 140;
            const failed = bucket.failed / max * 140;
            const other = (bucket.count - bucket.completed - bucket.failed) / max * 140;
            return <g key={bucket.at}><title>{timestamp(bucket.at)}: {bucket.count} turns, {bucket.completed} completed, {bucket.failed} failed</title><rect x={42 + i * 76} y={160 - completed} width="48" height={completed} className="obs-chart-completed" /><rect x={42 + i * 76} y={160 - completed - failed} width="48" height={failed} className="obs-chart-failed" /><rect x={42 + i * 76} y={160 - completed - failed - other} width="48" height={other} className="obs-chart-other" /></g>;
          })}
          <text x="30" y="185">{new Date(s.since).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</text><text x="950" y="185" textAnchor="end">{new Date(s.until).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</text>
        </svg>
        <figcaption><small>Completed</small><small>Failed</small><small>Running, waiting or cancelled</small></figcaption>
      </figure>}
    </section>
    <section className="obs-metrics-grid">
      <section className="obs-metric-section"><h2>Response latency</h2><p className="obs-note">Agent: completed turns. HTTP: successful requests, latest {number(s.request_limit)}; inspector traffic excluded. Durations overlap.</p><section className="table-scroll"><table><thead><tr><th>Measurement</th><th>p50</th><th>p95</th><th>Samples</th></tr></thead><tbody>{Object.entries(s.latency).map(([key, value]) => <tr key={key}><th scope="row">{key === "agent" ? "Agent active" : key === "client" ? "Browser (advisory)" : "Server request"}</th><td>{duration(value.p50_ms)}</td><td>{duration(value.p95_ms)}</td><td>{number(value.count)}</td></tr>)}</tbody></table></section><p className="obs-note">Human waiting is excluded from agent time. Missing browser reports stay unknown.</p></section>
      <section className="obs-metric-section"><h2>Provider usage</h2><p className="obs-note">Model and Decisions attempts in this turn cohort. Known tokens only; coverage is shown for every field.</p><section className="table-scroll"><table><thead><tr><th>Token field</th><th>Recorded total</th><th>Calls with usage</th></tr></thead><tbody>{Object.entries(s.usage).map(([key, value]) => <tr key={key}><th scope="row">{label(key)}</th><td>{number(value.total)}</td><td>{value.known} / {s.provider_calls}</td></tr>)}</tbody></table></section><p className="obs-note">Cached input and reasoning tokens are subsets, never added to input/output totals.</p></section>
      <section className="obs-metric-section"><h2>Action timings</h2><p className="obs-note">Individual attempts across all outcomes. Nested spans overlap with agent time.</p><section className="table-scroll"><table><thead><tr><th>Action</th><th>p50</th><th>p95</th><th>Samples</th></tr></thead><tbody>{s.stages.map(stage => <tr key={stage.name}><th scope="row">{label(stage.name)}</th><td>{duration(stage.p50_ms)}</td><td>{duration(stage.p95_ms)}</td><td>{number(stage.count)}</td></tr>)}</tbody></table></section>{!s.stages.length && <p className="obs-note">No timed actions recorded in this window.</p>}</section>
      <section className="obs-metric-section"><h2>Operational signals</h2><dl className="obs-signals"><dt>Searches with no results</dt><dd>{s.no_results} / {s.searches} <small>({rate(s.no_results, s.searches)})</small></dd><dt>Turns that requested clarification</dt><dd>{s.clarified_turns} / {s.count} <small>({rate(s.clarified_turns, s.count)})</small></dd><dt>Corrections and retry events</dt><dd>{number(s.corrections_and_retries)}</dd><dt>HTTP errors (4xx + 5xx)</dt><dd>{s.http_errors} / {s.requests}</dd><dt>Recorded action events</dt><dd>{number(s.events)}</dd></dl></section>
    </section>
    <section className="obs-metric-section"><HStack hAlign="between" vAlign="center" gap={3}><h2>Recent traces</h2><Button label="Browse traces" variant="ghost" size="sm" onClick={onTraces} /></HStack><section className="table-scroll"><table><thead><tr><th>Question</th><th>Outcome</th><th>Total tokens</th><th>Agent active</th><th>Started</th></tr></thead><tbody>{runs.slice(0, 6).map(run => <tr key={run.id}><td><button className="obs-text-button" onClick={() => onRun(run.id)}>{run.question}</button><small>Session {run.conversation_id.slice(0, 8)} · Turn {run.id.slice(0, 8)}</small></td><td className={`obs-status obs-${run.status}`}>{label(run.status)}</td><td>{number(queryTokens(run))}<small>{number(run.input_tokens)} in / {number(run.output_tokens)} out</small></td><td>{duration(run.active_ms)}</td><td>{timestamp(run.created_at)}</td></tr>)}</tbody></table></section>{!runs.length && <p className="obs-note">No saved traces in this window.</p>}</section>
  </VStack>;
}
