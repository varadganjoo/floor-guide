import test from 'node:test';
import assert from 'node:assert/strict';
import { executionTimeline, rate, number, queryTokens } from '../src/lib/observability.ts';

const event = (id, execution, parent, time, duration) => ({
  id, span_id: id, execution_id: execution, parent_span_id: parent,
  created_at: time, duration_ms: duration, event: 'model_call', payload: {},
});

test('waterfall separates execution segments across a long clarification wait', () => {
  const segments = executionTimeline([
    event('root', 'first', null, '2026-11-23T10:00:00Z', null),
    event('child', 'first', 'root', '2026-11-23T10:00:01Z', 500),
    event('resume', 'second', null, '2026-11-23T12:00:00Z', null),
    event('answer', 'second', 'resume', '2026-11-23T12:00:02Z', 1000),
  ]);
  assert.equal(segments.length, 2);
  assert.equal(segments[0].duration, 1000);
  assert.equal(segments[1].duration, 2000);
  assert.equal(segments[0].rows[1].offset, 50);
  assert.equal(segments[0].rows[1].width, 50);
  assert.equal(segments[0].rows[1].depth, 1);
});

test('point-only events and cyclic parents never produce invalid bars', () => {
  const segments = executionTimeline([
    event('one', 'execution', 'two', '2026-11-23T10:00:00', null),
    event('two', 'execution', 'one', '2026-11-23T10:00:00Z', null),
  ]);
  assert.equal(segments[0].duration, 0);
  for (const row of segments[0].rows) {
    assert.equal(row.offset, 0);
    assert.equal(row.width, 0);
    assert.ok(row.depth <= 1);
  }
  assert.deepEqual(executionTimeline([]), []);
});

test('unknown data and empty populations remain distinct from measured zero', () => {
  assert.equal(number(null), 'Unknown');
  assert.equal(number(0), '0');
  assert.equal(rate(0, 0), '—');
  assert.equal(rate(0, 4), '0.0%');
});

test('per-query totals require both measured input and output usage', () => {
  assert.equal(queryTokens({input_tokens: 1200, output_tokens: 340}), 1540);
  assert.equal(queryTokens({input_tokens: 0, output_tokens: 0}), 0);
  assert.equal(queryTokens({input_tokens: 1200, output_tokens: null}), null);
  assert.equal(queryTokens({input_tokens: null, output_tokens: 340}), null);
});
